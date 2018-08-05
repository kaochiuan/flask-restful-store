from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate, MigrateCommand


app = Flask(__name__)
api = Api(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://iptech:CoffeeIpTech@127.0.0.1/coffee_cloud?charset=utf8&local_infile=1"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'Coffee@IpTech'

db = SQLAlchemy(app)
migrate = Migrate(app=app, db=db)


@app.before_first_request
def create_tables():
    db.create_all()


app.config['JWT_SECRET_KEY'] = 'jwt@IpTech'
jwt = JWTManager(app)

app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
app.config['JWT_EXPIRATION_DELTA'] = 3600


@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    return models.RevokedTokenModel.is_jti_blacklisted(jti)


import views, models, resources

api.add_resource(resources.UserRegistration, '/registration')
api.add_resource(resources.UserLogin, '/login')
api.add_resource(resources.UserLogoutAccess, '/logout/access')
api.add_resource(resources.UserLogoutRefresh, '/logout/refresh')
api.add_resource(resources.UserResetPassword, '/user/reset_password')
api.add_resource(resources.TokenRefresh, '/token/refresh')
api.add_resource(resources.AllUsers, '/users')
api.add_resource(resources.SecretResource, '/secret')
api.add_resource(resources.MenuResource, '/menu')
api.add_resource(resources.OrderResource, '/order')
api.add_resource(resources.SerialNumberResource, '/serial_number')
