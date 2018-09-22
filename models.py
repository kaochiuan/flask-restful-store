import enum
import datetime
from run import db
from passlib.hash import pbkdf2_sha256 as sha256


class DBEnum(enum.Enum):
    @classmethod
    def get_enum_labels(cls):
        return [i.value for i in cls]

    @classmethod
    def has_value(cls, val):
        return any(val == item.value for item in cls)


class Gender(DBEnum):
    NONE = 'none'
    MALE = 'male'
    FEMALE = 'female'


class MenuTypes(DBEnum):
    CUSTOMIZED = 'customized'
    GENERAL = 'general'


class FoamLevels(DBEnum):
    NONE = 'none'
    STANDARD = 'standard'
    THICK = 'thick'


class SizeLevels(DBEnum):
    FINE = 'fine'
    MEDIUM = 'medium'
    COARSE = 'coarse'


class WaterLevels(DBEnum):
    LONG = 'long'
    STANDARD = 'standard'
    SMALL = 'small'


class TasteLevels(DBEnum):
    MILD = 'mild'
    STANDARD = 'standard'
    STRONG = 'strong'


class UserModel(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.Enum(*Gender.get_enum_labels()), default=Gender.NONE.value)  # gender
    birthday = db.Column(db.Date, nullable=True)
    email = db.Column(db.String(255), nullable=False, default="")
    menu_list = db.relationship('MenuModel', back_populates='owner', lazy=True)
    order_list = db.relationship('OrderModel', back_populates='owner', lazy=True)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def get_by_id(cls, user_id: int):
        return cls.query.get(user_id)

    @classmethod
    def return_all(cls):
        def to_json(x):
            return {
                'username': x.username,
                'email': x.email
            }

        return {'users': list(map(lambda x: to_json(x), UserModel.query.all()))}

    @classmethod
    def delete_all(cls):
        try:
            num_rows_deleted = db.session.query(cls).delete()
            db.session.commit()
            return {'message': '{} row(s) deleted'.format(num_rows_deleted)}
        except:
            return {'message': 'Something went wrong'}

    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, hash_value):
        return sha256.verify(password, hash_value)


class RevokedTokenModel(db.Model):
    __tablename__ = 'revoked_tokens'
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(120))

    def add(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def is_jti_blacklisted(cls, jti):
        query = cls.query.filter_by(jti=jti).first()
        return bool(query)


class AssociationModel(db.Model):
    __tablename_ = 'association_menu_order'
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.id'), primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), primary_key=True)
    counts = db.Column(db.Integer, default=0)
    menu = db.relationship('MenuModel', back_populates='orders')
    order = db.relationship('OrderModel', back_populates='menus')


class MenuModel(db.Model):
    __tablename__ = 'menu'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    menu_type = db.Column(db.Enum(*MenuTypes.get_enum_labels()), default=MenuTypes.CUSTOMIZED.value)  # menu type
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    taste_level = db.Column(db.Enum(*TasteLevels.get_enum_labels()), default=TasteLevels.STANDARD.value)  # taste level
    water_level = db.Column(db.Enum(*WaterLevels.get_enum_labels()), default=WaterLevels.STANDARD.value)  # water level
    foam_level = db.Column(db.Enum(*FoamLevels.get_enum_labels()), default=FoamLevels.STANDARD.value)  # foam level
    grind_size = db.Column(db.Enum(*SizeLevels.get_enum_labels()), default=SizeLevels.MEDIUM.value)  # particle size
    create_date = db.Column(db.DATETIME, default=datetime.datetime.utcnow())
    owner = db.relationship('UserModel', back_populates='menu_list')
    orders = db.relationship('AssociationModel', back_populates='menu')
    serials = db.relationship('SerialNumberModel', back_populates='menu')

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_user(cls, owner: UserModel):
        return cls.query.filter_by(owner_id=owner.id)

    @classmethod
    def get_by_owner_and_id(cls, menu_id: int, owner: UserModel):
        return cls.query.filter_by(id=menu_id, owner_id=owner.id).one_or_none()

    @classmethod
    def get_by_id(cls, menu_id: int):
        return cls.query.get(menu_id)


class OrderModel(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    create_date = db.Column(db.DATETIME, default=datetime.datetime.utcnow())
    customized_message = db.Column(db.String(255))
    serial_number_list = db.relationship('SerialNumberModel', back_populates='order', lazy=True)
    owner = db.relationship('UserModel', back_populates='order_list')
    menus = db.relationship('AssociationModel', back_populates='order')
    is_obsolete = db.Column(db.Boolean, default=False)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls, order_id: int):
        return cls.query.get(order_id)

    @classmethod
    def find_valid_by_user(cls, user: UserModel):
        return cls.query.filter_by(user_id=user.id, is_obsolete=False)

    @classmethod
    def find_history_by_user(cls, user: UserModel):
        return cls.query.filter_by(user_id=user.id, is_obsolete=True)


class SerialNumberModel(db.Model):
    __tablename__ = 'serial_number'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.id'), nullable=False)
    serial_number = db.Column(db.String(255), nullable=False)
    create_date = db.Column(db.DATETIME, default=datetime.datetime.utcnow())
    order = db.relationship('OrderModel', back_populates='serial_number_list')
    menu = db.relationship('MenuModel', back_populates='serials')

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_order(cls, order: OrderModel):
        return cls.query.filter_by(order_id=order.id)

    @classmethod
    def get_by_id(cls, serial_id: int):
        return cls.query.get(serial_id)

    @classmethod
    def get_by_serial_number(cls, serial_number: str):
        db_result = cls.query.filter_by(serial_number=serial_number).first()

        result = None
        if db_result:
            result = {'order_id': db_result.order_id, 'menu_id': db_result.menu_id}

        return result
