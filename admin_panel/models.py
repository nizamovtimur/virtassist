from config import app
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy import BigInteger, Column, DateTime, Engine, ForeignKey, Text, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship
from pgvector.sqlalchemy import Vector


db = SQLAlchemy(app)
app.app_context().push()


class Base(DeclarativeBase):
    """Базовый класс модели, который инициализирует общие поля.

    Args:
        time_created (datetime): время создания модели
        time_updated (datetime): время обновления модели
    """

    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())


class Chunk(Base):
    """Фрагмент документа из вики-системы

    Args:
        confluence_url (str): ссылка на источник
        text (str): текст фрагмента
        embedding (Vector): векторное представление текста фрагмента
    """

    __tablename__ = "chunk"
    id: Mapped[int] = mapped_column(primary_key=True)
    confluence_url: Mapped[str] = mapped_column(Text(), index=True)
    text: Mapped[str] = mapped_column(Text())
    embedding: Mapped[Vector] = mapped_column(Vector(312))


class User(Base):
    """Пользователь чат-бота

    Args:
        id (int): id пользователя
        vk_id (int | None): id пользователя ВКонтакте
        telegram_id (int | None): id пользователя Telegram
        vk_id (int | None): id пользователя ВКонтакте
    """

    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vk_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True)
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True)
    is_subscribed: Mapped[bool] = mapped_column()

    question_answers: Mapped[List["QuestionAnswer"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", order_by="desc(QuestionAnswer.time_created)")


class QuestionAnswer(Base):
    """Вопрос пользователя с ответом на него

    Args:
        id (int): id ответа
        question (str): вопрос пользователя
        answer (str): ответ на вопрос пользователя
        confluence_url (str): ссылка на страницу в вики-системе, содержащую ответ
        score (int): оценка пользователем ответа
        user_id (int): id пользователя, задавшего вопрос
    """

    __tablename__ = "question_answer"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(Text())
    answer: Mapped[Optional[str]] = mapped_column(Text())
    confluence_url: Mapped[Optional[str]] = mapped_column(Text(), index=True)
    score: Mapped[Optional[int]] = mapped_column()
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))

    user: Mapped["User"] = relationship(back_populates="question_answers")
