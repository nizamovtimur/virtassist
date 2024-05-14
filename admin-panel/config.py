import os
import json
from dotenv import load_dotenv
from flask import Flask


load_dotenv("../.env")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}/{os.getenv('POSTGRES_DB')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["CHATBOT_HOST"] = os.getenv("CHATBOT_HOST")
app.config["QA_HOST"] = os.getenv("QA_HOST")
app.config["ABBREVIATION_UTMN"] = os.getenv("ABBREVIATION_UTMN").split(" ")
app.config["OIDC_CLIENT_SECRETS"] = {
    "web": {
        "issuer": os.getenv("ISSUER"),
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
        # "auth_uri": os.getenv("AUTH_URI"),
        "userinfo_uri": os.getenv("USERINFO"),
        "redirect_uris": [os.getenv("REDIRECTS")],
    }
}
