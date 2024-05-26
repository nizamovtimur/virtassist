import os
from dotenv import load_dotenv
from flask import Flask


load_dotenv("../.env")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}/{os.getenv('POSTGRES_DB')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["CHATBOT_HOST"] = os.getenv("CHATBOT_HOST")
app.config["QA_HOST"] = os.getenv("QA_HOST")
# app.config["ABBREVIATION_UTMN"] = os.getenv("ABBREVIATION_UTMN").split(" ")
app.config["ABBREVIATION_UTMN"] = (
    "тюмгу шкн игип фэи соцгум ипип биофак инзем инхим фти инбио ифк ед шпи шен уиот".split(
        " "
    )
)
