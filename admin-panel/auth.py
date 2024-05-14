from flask_oidc import OpenIDConnect
from config import app

oidc = OpenIDConnect(app)
