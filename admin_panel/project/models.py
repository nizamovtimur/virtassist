from config import app
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy(app)
app.app_context().push()

class Chunk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column("confluence_url", db.Text)
    text = db.Column("text", db.Text)
    #embedding = db.Column("embedding", db.Vector)
    #time_crt = db.Column("time_created", db.Timestamp)
    #time_upd = db.Column("time_updated", db.Timestamp)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vk_id = db.Column("vk_id", db.BigInteger)
    tg_id = db.Column("telegram_id", db.BigInteger)
    is_sub = db.Column("is_subscribed", db.Boolean)
    #time_crt = db.Column("time_created", db.Timestamp)
    #time_upd = db.Column("time_updated", db.Timestamp)

class QuestionAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column("question", db.Text)
    answer = db.Column("answer", db.Text)
    url = db.Column("confluence_url", db.Text)
    score = db.Column("score", db.Integer)
    #user_id = db.relationship("User", backref="user_id")
    #time_crt = db.Column("time_created", db.Timestamp)
    #time_upd = db.Column("time_updated", db.Timestamp)
