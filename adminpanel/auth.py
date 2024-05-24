from flask_login import LoginManager, UserMixin
from bcrypt import hashpw

from config import app

from models import Admin

login_manager = LoginManager()
login_manager.init_app(app)


pwhash = hashpw(login_data['password'], user.password)
if user.password == pwhash:
    print 'Access granted'

# class User(UserMixin):
#     def __init__(self, email, password):
#         self.id = email
#         self.password = password


users = {"leafstorm": [Admin.id, Admin.password]}


@login_manager.user_loader
def user_loader(id):
    return users.get(id)
