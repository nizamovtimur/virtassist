from flask import Flask
from dotenv import load_dotenv
import os


load_dotenv('virtassist/.env')

app = Flask(__name__)
#app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}/{os.getenv('POSTGRES_DB')}"
app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}/test_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
