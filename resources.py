from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required,
                                get_jwt_identity, get_raw_jwt)
from flask_restful import Resource
from models import UserModel, RevokedTokenModel, MenuModel, OrderModel, AssociationModel, SerialNumberModel
from models import MenuTypes, FoamLevels, SizeLevels, TasteLevels, WaterLevels, Gender
import logging
import datetime
from logging.handlers import RotatingFileHandler
from webargs.flaskparser import use_args
from webargs import validate
from marshmallow import Schema, fields


logging.basicConfig(datefmt='%m-%d %H:%M',
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    handlers=[RotatingFileHandler(filename='coffee_cloud.log', mode='a', maxBytes=1 * 1024 * 1024,
                                                  backupCount=7, encoding='utf8'), ])

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


class OrderSchema(Schema):
    menu_id = fields.Int()
    counts = fields.Int()

    class Meta:
        strict = True


user_args = {
    'username': fields.Str(required=True),
    'password': fields.Str(required=True),
    'email': fields.Str(required=False)
}


class UserRegistration(Resource):
    @use_args(user_args)
    def post(self, args):
        if UserModel.find_by_username(args.get('username')):
            return {'message': 'User {} already exists.'.format(args.get('username'))}, 400

        new_user = UserModel(
            username=args.get('username'),
            password=UserModel.generate_hash(args.get('password')),
            email=args.get('email'),
        )
        try:
            new_user.save_to_db()
            access_token = create_access_token(identity=args.get('username'))
            refresh_token = create_refresh_token(identity=args.get('username'))
            return {
                'message': 'User {} was created'.format(args.get('username')),
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        except:
            return {'message': 'Something went wrong'}, 500


class UserLogin(Resource):
    @use_args(user_args)
    def post(self, args):
        current_user = UserModel.find_by_username(args.get('username'))
        if not current_user:
            return {'message': 'User {} doesn\'t exist'.format(args.get('username'))}

        if UserModel.verify_hash(args.get('password'), current_user.password):
            access_token = create_access_token(identity=args.get('username'))
            refresh_token = create_refresh_token(identity=args.get('username'))
            return {
                'message': 'User {} was logged-in'.format(args.get('username')),
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        else:
            return {'message': 'Wrong credentials'}, 404


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
        current_user = UserModel.find_by_username(args.get('username'))
        if not current_user:
            return {'message': 'User {} doesn\'t exist'.format(args.get('username'))}

        if UserModel.verify_hash(args.get('password'), current_user.password):
            current_user.password = UserModel.generate_hash(args.get('new_password'))
            try:
                current_user.save_to_db()
                access_token = create_access_token(identity=args.get('username'))
                refresh_token = create_refresh_token(identity=args.get('username'))
                return {
                    'message': 'User {}: Your password has been reset'.format(args.get('username')),
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


class UserProfileRoute(Resource):
    @jwt_required
    def get(self, user_id=None):
        if not user_id:
            return {'message': 'user not found'}, 404

        user = UserModel.get_by_id(user_id)
        if user:
            return {'username': user.username, 'email': user.email,
                    'phone': user.phone, 'gender': user.gender,
                    'birthday': str(user.birthday)}
        else:
            return {'message': 'user not found'}, 404


class UserProfile(Resource):
    profile_args = {
        'gender': fields.Str(required=True, validate=validate.OneOf(Gender.get_enum_labels())),
        'phone': fields.Str(required=True),
        'birthday': fields.Date(required=True)
    }

    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = UserModel.find_by_username(current_user)
        if user:
            return {'username': user.username, 'email': user.email,
                    'phone': user.phone, 'gender': user.gender,
                    'birthday': str(user.birthday)}
        else:
            return {'message': 'user not found'}, 404

    @jwt_required
    @use_args(profile_args)
    def post(self, args):
        current_user = get_jwt_identity()
        user = UserModel.find_by_username(current_user)

        if user:
            try:
                if args:
                    user.birthday = args.get('birthday')
                    user.phone = args.get('phone')
                    user.gender = args.get('gender')
                    user.save_to_db()
                    return {'message': 'user {}: profile has been updated.'.format(user.username)}
                else:
                    return {'message': 'wrong parameters'}, 400
            except:
                return {'message': 'Something went wrong'}, 500

        else:
            return {'message': 'user not found'}, 404


class TokenRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(identity=current_user)
        return {'access_token': access_token}


class MenuResource(Resource):
    menu_args = {
        'menu_id': fields.Int(required=False),
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
            logger.exception('Menu registration failed.')
            return {'message': 'Something went wrong'}, 500

    @use_args(menu_args, locations=('form', 'json'))
    @jwt_required
    def patch(self, args):
        current_user = get_jwt_identity()
        logged_user = UserModel.find_by_username(current_user)

        if not args.get('menu_id'):
            return {'message': 'menu_id is required.'}, 400

        db_result = MenuModel.get_by_owner_and_id(menu_id=args.get('menu_id'), owner=logged_user)

        if db_result:
            try:
                db_result.name = args.get('name')
                db_result.menu_type = args.get('menu_type')
                db_result.taste_level = args.get('taste_level')
                db_result.water_level = args.get('water_level')
                db_result.foam_level = args.get('foam_level')
                db_result.grind_size = args.get('grind_size')
                db_result.save_to_db()
                return {'message': 'menu update successfully.'}
            except Exception as ex:
                logger.exception('Menu update failed.')
                return {'message': 'Something went wrong'}, 500
        else:
            return {'message': 'menu item not found.'}, 404

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


class OrderResourceRoute(Resource):
    @jwt_required
    def get(self, order_id=None):
        if not order_id:
            return {'message': 'user not found'}, 404

        order = OrderModel.get_by_id(order_id)
        if order:
            if order.is_obsolete and order.id != 1:
                return {'message': 'order was obsoleted'}, 400
            else:
                menu_list = list()
                for menu in order.menus:
                    menu_list.append({'menu_id': menu.menu.id,
                                      'menu_name': menu.menu.name,
                                      'taste_level': menu.menu.taste_level,
                                      'water_level': menu.menu.water_level,
                                      'foam_level': menu.menu.foam_level,
                                      'grind_size': menu.menu.grind_size,
                                      'menu_type': menu.menu.menu_type,
                                      'counts': menu.counts})
                return {'order_id': order.id, 'order_contents': menu_list,
                        'order_date': order.create_date.strftime("%Y-%m-%d %H:%M:%S")}
        else:
            return {'message': 'order not found'}, 404

    def patch(self, order_id=None):
        if not order_id:
            return {'message': 'order not found'}, 404

        order = OrderModel.get_by_id(order_id)
        if order:
            order.is_obsolete = True
            order.save_to_db()
            return {'order_id': order.id, 'is_obsoleted': order.is_obsolete}
        else:
            return {'message': 'user not found'}, 404


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
            new_order = OrderModel(user_id=logged_user.id,
                                   customized_message=received_item.get("message"),
                                   create_date=datetime.datetime.utcnow())

            for item in received_item.get("order"):
                found_menu = MenuModel.get_by_id(item.get("menu_id"))
                a = AssociationModel(counts=item.get("counts"))
                a.menu = found_menu
                new_order.menus.append(a)

            new_order.save_to_db()
            result = {"message": "successful"}
        except Exception as ex:
            logger.exception("create order failed")
            result = {"message": "failed"}
        return result

    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        logged_user = UserModel.find_by_username(current_user)

        db_result = OrderModel.find_valid_by_user(logged_user)

        result = list()
        for item in db_result:
            menu_list = list()
            for menu in item.menus:
                menu_list.append({'menu_id': menu.menu.id,
                                  'menu_name': menu.menu.name,
                                  'taste_level': menu.menu.taste_level,
                                  'water_level': menu.menu.water_level,
                                  'foam_level': menu.menu.foam_level,
                                  'grind_size': menu.menu.grind_size,
                                  'menu_type': menu.menu.menu_type,
                                  'counts': menu.counts})
            result.append({'order_id': item.id, 'order_contents': menu_list,
                           'order_date': item.create_date.strftime("%Y-%m-%d %H:%M:%S")})

        return result


class SerialNumberResource(Resource):
    serial_args = {
        'order_id': fields.Int(),
        'menu_id': fields.Int(),
        'serial_number': fields.Str(required=True)
    }

    serial_by_order_arg = {
        'order_id': fields.Int(required=False),
        'serial_number': fields.Str(required=False)
    }

    @use_args(serial_args, locations=('form', 'json'))
    @jwt_required
    def post(self, received_link):
        order_id = received_link.get("order_id")
        serial_number = received_link.get("serial_number")
        menu_id = received_link.get("menu_id")
        duplicated = SerialNumberModel.find_duplicate_link(order_id=order_id,
                                                           serial_number=serial_number,
                                                           menu_id=menu_id)

        if not duplicated:
            serial_link = SerialNumberModel(order_id=order_id,
                                            serial_number=serial_number,
                                            menu_id=menu_id)
            try:
                serial_link.save_to_db()
                result = {"message": "link serial success."}
            except Exception as ex:
                logger.excption("link serial failed")
                result = {"message": "link failed", "reason": "exception raised."}
        else:
            result = {"message": "link failed", "reason": "duplicated link information"}

        return result

    @use_args(serial_by_order_arg)
    @jwt_required
    def get(self, received):
        order_id = received.get('order_id')
        serial_number_str = received.get('serial_number')

        result = list()
        if order_id:
            order = OrderModel.get_by_id(order_id=received.get('order_id'))
            if order:
                db_result = SerialNumberModel.find_by_order(order=order)
                for item in db_result:
                    result.append({'serial_number': item.serial_number, 'menu_id': item.menu.id, 'order_id': item.order.id})
            else:
                return {'message': 'order_id not found'}, 404
        elif serial_number_str:
            serial = SerialNumberModel.get_by_serial_number(serial_number=serial_number_str)

            if serial:
                logging.error(serial.order.customized_message)
                result = {'serial_number': serial.serial_number, 'customized_message': serial.order.customized_message}
            else:
                return {'message': 'serial_number not found'}, 404
        else:
            return {'message': 'order or serial is required.'}, 400

        return result
