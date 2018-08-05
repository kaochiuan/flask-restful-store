from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required,
                                get_jwt_identity, get_raw_jwt)
from flask_restful import Resource
from models import UserModel, RevokedTokenModel, MenuModel, OrderModel, AssociationModel, SerialNumberModel
from models import MenuTypes, FoamLevels, SizeLevels, TasteLevels, WaterLevels
import logging
from webargs.flaskparser import use_args
from webargs import validate
from marshmallow import Schema, fields

logging.basicConfig(datefmt='%m-%d %H:%M',
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    handlers=[logging.FileHandler('coffee_cloud.log', 'w', 'utf-8'), ])

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


class OrderSchema(Schema):
    menu_id = fields.Int()
    counts = fields.Int()

    class Meta:
        strict = True


user_args = {
    'username': fields.Str(required=True),
    'password': fields.Str(required=True)
}


class UserRegistration(Resource):
    @use_args(user_args)
    def post(self, args):
        if UserModel.find_by_username(args['username']):
            return {'message': 'User {} already exists.'.format(args['username'])}

        new_user = UserModel(
            username=args['username'],
            password=UserModel.generate_hash(args['password'])
        )
        try:
            new_user.save_to_db()
            access_token = create_access_token(identity=args['username'])
            refresh_token = create_refresh_token(identity=args['username'])
            return {
                'message': 'User {} was created'.format(args['username']),
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        except:
            return {'message': 'Something went wrong'}, 500


class UserLogin(Resource):
    @use_args(user_args)
    def post(self, args):
        current_user = UserModel.find_by_username(args['username'])
        if not current_user:
            return {'message': 'User {} doesn\'t exist'.format(args['username'])}

        if UserModel.verify_hash(args['password'], current_user.password):
            access_token = create_access_token(identity=args['username'])
            refresh_token = create_refresh_token(identity=args['username'])
            return {
                'message': 'User {} was logged-in'.format(args['username']),
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        else:
            return {'message': 'Wrong credentials'}


class UserLogoutAccess(Resource):
    @jwt_required
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = RevokedTokenModel(jti=jti)
            revoked_token.add()
            return {'message': 'Access token has been revoked'}
        except:
            return {'message': 'Something went wrong'}, 500


class UserResetPassword(Resource):
    reset_pwd_args = {
        'username': fields.Str(required=True),
        'password': fields.Str(required=True),
        'new_password': fields.Str(required=True)
    }

    @jwt_required
    @use_args(reset_pwd_args)
    def post(self, args):
        current_user = UserModel.find_by_username(args['username'])
        if not current_user:
            return {'message': 'User {} doesn\'t exist'.format(args['username'])}

        if UserModel.verify_hash(args['password'], current_user.password):
            current_user.password = UserModel.generate_hash(args['new_password'])
            try:
                current_user.save_to_db()
                access_token = create_access_token(identity=args['username'])
                refresh_token = create_refresh_token(identity=args['username'])
                return {
                    'message': 'User {}: Your password has been reset'.format(args['username']),
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }
            except:
                return {'message': 'Something went wrong'}, 500
        else:
            return {'message': 'username or password is incorrect'}, 400


class UserLogoutRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = RevokedTokenModel(jti=jti)
            revoked_token.add()
            return {'message': 'Refresh token has been revoked'}
        except:
            return {'message': 'Something went wrong'}, 500


class TokenRefresh(Resource):
    def post(self):
        return {'message': 'Token refresh'}


class AllUsers(Resource):
    def get(self):
        return {'message': 'List of users'}

    def delete(self):
        return {'message': 'Delete all users'}


class SecretResource(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        return {
            'user': current_user,
            'answer': 42
        }


class TokenRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(identity=current_user)
        return {'access_token': access_token}


class MenuResource(Resource):
    menu_args = {
        'name': fields.Str(required=True),
        'menu_type': fields.Str(required=True, validate=validate.OneOf(MenuTypes.get_enum_labels())),
        'taste_level': fields.Str(required=True, validate=validate.OneOf(TasteLevels.get_enum_labels())),
        'water_level': fields.Str(required=True, validate=validate.OneOf(WaterLevels.get_enum_labels())),
        'foam_level': fields.Str(required=True, validate=validate.OneOf(FoamLevels.get_enum_labels())),
        'grind_size': fields.Str(required=True, validate=validate.OneOf(SizeLevels.get_enum_labels()))
    }

    @use_args(menu_args, locations=('form', 'json'))
    @jwt_required
    def post(self, args):
        current_user = get_jwt_identity()
        logged_user = UserModel.find_by_username(current_user)

        new_menu = MenuModel(name=args.get('name'),
                             menu_type=args.get('menu_type'),
                             taste_level=args.get('taste_level'),
                             water_level=args.get('water_level'),
                             foam_level=args.get('foam_level'),
                             grind_size=args.get('grind_size'),
                             owner_id=logged_user.id)
        try:
            new_menu.save_to_db()
            return {'message': 'New menu created successfully.'}
        except Exception as ex:
            logger.error('Menu registration failed.', ex)
            return {'message': 'Something went wrong'}, 500

    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        logged_user = UserModel.find_by_username(current_user)

        db_result = MenuModel.find_by_user(logged_user)

        result = list()
        for item in db_result:
            result.append(
                {'menu_id': item.id, 'name': item.name,
                 'water_level': item.water_level, 'foam_level': item.foam_level,
                 'taste_level': item.taste_level, 'grind_size': item.grind_size,
                 'menu_type': item.menu_type})
        return result


class OrderResource(Resource):
    order_args = {
        'message': fields.Str(required=True),
        'order': fields.Nested(OrderSchema, many=True)
    }

    @use_args(order_args)
    @jwt_required
    def post(self, received_item):
        current_user = get_jwt_identity()
        logged_user = UserModel.find_by_username(current_user)

        try:
            new_order = OrderModel(user_id=logged_user.id, customized_message=received_item.get("message"))

            for item in received_item.get("order"):
                found_menu = MenuModel.get_by_id(item.get("menu_id"))
                a = AssociationModel(counts=item.get("counts"))
                a.menu = found_menu
                new_order.menus.append(a)

            new_order.save_to_db()
            result = "successful"
        except Exception as ex:
            logger.error("create order failed", ex)
            result = "failed"
        return result

    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        logged_user = UserModel.find_by_username(current_user)

        db_result = OrderModel.find_by_user(logged_user)

        result = list()
        for item in db_result:
            menu_list = list()
            for menu in item.menus:
                menu_list.append({'menu_id': menu.menu.id, 'counts': menu.counts})
            result.append({'order_id': item.id, 'order_contents': menu_list})

        return result


class SerialNumberResource(Resource):
    serial_args = {
        'order_id': fields.Int(),
        'menu_id': fields.Int(),
        'serial_number': fields.Str(required=True)
    }

    serial_by_order_arg = {
        'order_id': fields.Int(required=True)
    }

    @use_args(serial_args)
    @jwt_required
    def post(self, received_link):
        serial_link = SerialNumberModel(order_id=received_link.get("order_id"),
                                        serial_number=received_link.get("serial_number"),
                                        menu_id=received_link.get("menu_id"))
        try:
            serial_link.save_to_db()
            result = "link serial success."
        except Exception as ex:
            logger.error("link serial failed", ex)
            result = "failed"

        return result

    @use_args(serial_by_order_arg)
    @jwt_required
    def get(self, received):
        order = OrderModel.get_by_id(order_id=received.get('order_id'))
        db_result = SerialNumberModel.find_by_order(order=order)

        result = list()

        for item in db_result:
            result.append({'serial_number': item.serial_number, 'menu_id': item.menu.id})

        return result

