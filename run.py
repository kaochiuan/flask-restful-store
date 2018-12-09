from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate


app = Flask(__name__)
api = Api(app=app)

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://iptech:CoffeeIpTech@127.0.0.1/coffee_cloud?charset=utf8&local_infile=1"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'Coffee@IpTech'
app.config['PROPAGATE_EXCEPTIONS'] = True

db = SQLAlchemy(app, use_native_unicode='utf8')
migrate = Migrate(app=app, db=db)


@app.before_first_request
def create_tables():
    db.create_all()


app.config['JWT_SECRET_KEY'] = 'jwt@IpTech'
jwt = JWTManager(app)

app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)


@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    return models.RevokedTokenModel.is_jti_blacklisted(jti)


import models
import resources


api.add_resource(resources.UserRegistration, '/user/registration')
api.add_resource(resources.UserLogin, '/login')
api.add_resource(resources.UserLogoutAccess, '/logout/access')
api.add_resource(resources.UserLogoutRefresh, '/logout/refresh')
api.add_resource(resources.UserResetPassword, '/user/reset_password')
api.add_resource(resources.TokenRefresh, '/token/refresh')
api.add_resource(resources.UserProfileRoute, '/user/', '/user/<int:user_id>', endpoint='user_id')
api.add_resource(resources.UserProfile, '/user_profile')
api.add_resource(resources.MenuResource, '/menu')
api.add_resource(resources.OrderResourceRoute, '/order/<int:order_id>', endpoint='order_id')
api.add_resource(resources.OrderResource, '/order')
api.add_resource(resources.SerialNumberResource, '/serial_number')
