from config import app
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy(app)
app.app_context().push()


class Chunk(db.Model):
    """Фрагмент документа из вики-системы

    Args:
        url (str): ссылка на источник
        text (str): текст фрагмента
    """
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column("confluence_url", db.Text)
    text = db.Column("text", db.Text)
    # embedding = db.Column("embedding", db.Vector)
    # time_crt = db.Column("time_created", db.Timestamp)
    # time_upd = db.Column("time_updated", db.Timestamp)


class User(db.Model):
    """Часть данных о пользователе

    Args:
        vk_id (int): id пользователя на платформе VK
        tg_id (int): id пользователя на платформе TG
        is_sub (bool): флаг подписки на рассылку
    """
    id = db.Column(db.Integer, primary_key=True)
    vk_id = db.Column("vk_id", db.BigInteger)
    tg_id = db.Column("telegram_id", db.BigInteger)
    is_sub = db.Column("is_subscribed", db.Boolean)
    # time_crt = db.Column("time_created", db.Timestamp)
    # time_upd = db.Column("time_updated", db.Timestamp)


class QuestionAnswer(db.Model):
    """Часть данных о вопросах и ответах

    Args:
        question (str): содержание вопроса
        answer (str): содержание ответа на заданный вопрос
        url (str): ссылка на страницу ответа на вики-систему
        score (int): 
    """
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column("question", db.Text)
    answer = db.Column("answer", db.Text)
    url = db.Column("confluence_url", db.Text)
    score = db.Column("score", db.Integer)
    # user_id = db.relationship("User", backref="user_id")
    # time_crt = db.Column("time_created", db.Timestamp)
    # time_upd = db.Column("time_updated", db.Timestamp)
