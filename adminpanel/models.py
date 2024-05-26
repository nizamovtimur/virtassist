import base64
from typing import Optional, List
from bcrypt import hashpw, gensalt, checkpw
from datetime import date, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Text, func, or_
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from config import app

db = SQLAlchemy(app)


class Chunk(db.Model):
    """Фрагмент документа из вики-системы

    Args:
        confluence_url (str): ссылка на источник
        text (str): текст фрагмента
        embedding (Vector): векторное представление текста фрагмента
        time_created (datetime): время создания модели
        time_updated (datetime): время обновления модели
    """

    __tablename__ = "chunk"

    id: Mapped[int] = mapped_column(primary_key=True)
    confluence_url: Mapped[str] = mapped_column(Text(), index=True)
    text: Mapped[str] = mapped_column(Text())
    embedding: Mapped[Vector] = mapped_column(Vector(312))

    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())


class User(db.Model):
    """Пользователь чат-бота

    Args:
        id (int): id пользователя
        vk_id (int | None): id пользователя ВКонтакте
        telegram_id (int | None): id пользователя Telegram
        vk_id (int | None): id пользователя ВКонтакте
        time_created (datetime): время создания модели
        time_updated (datetime): время обновления модели
    """

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vk_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True)
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True)
    is_subscribed: Mapped[bool] = mapped_column()

    question_answers: Mapped[List["QuestionAnswer"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(QuestionAnswer.time_created)",
    )

    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())


class QuestionAnswer(db.Model):
    """Вопрос пользователя с ответом на него

    Args:
        id (int): id ответа
        question (str): вопрос пользователя
        answer (str | None): ответ на вопрос пользователя
        confluence_url (str | None): ссылка на страницу в вики-системе, содержащую ответ
        score (int | None): оценка пользователем ответа
        user_id (int): id пользователя, задавшего вопрос
        time_created (datetime): время создания модели
        time_updated (datetime): время обновления модели
    """

    __tablename__ = "question_answer"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(Text())
    answer: Mapped[Optional[str]] = mapped_column(Text())
    confluence_url: Mapped[Optional[str]] = mapped_column(Text(), index=True)
    score: Mapped[Optional[int]] = mapped_column()
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))

    user: Mapped["User"] = relationship(back_populates="question_answers")

    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())


class Admin(db.Model, UserMixin):
    """Администратор панели

    Args:
        id (int): id ответа
        name (str): имя
        surname (str): фамилия
        last_name (str | None): отчество (опционально)
        email (str): корпоративная электронная почта
        department (str): подразделение
        time_created (datetime): время создания модели
        time_updated (datetime): время обновления модели
    """

    __tablename__ = "admin"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text())
    surname: Mapped[str] = mapped_column(Text())
    last_name: Mapped[Optional[str]] = mapped_column(Text())
    email: Mapped[str] = mapped_column(Text())
    department: Mapped[str] = mapped_column(Text())
    password_hash: Mapped[str] = mapped_column(Text(), nullable=False)

    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())

    def set_password(self, password: str) -> None:
        """Метод хеширования пароля администратора.

        Args:
            password (str): пароль администратора.
        """
        hashed = hashpw(password.encode("utf-8"), gensalt())
        self.password_hash = base64.b64encode(hashed).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Метод проверки введенного администратором пароля.

        Args:
            password (str): введенный администратором пароль.

        Returns:
            bool: проверка, совпадает ли введенный пароль с хешированным паролем.
        """
        hashed = base64.b64decode(self.password_hash.encode("utf-8"))
        return checkpw(password.encode("utf-8"), hashed)


def get_questions_for_clusters(
    time_start: str = str(date.today() - timedelta(days=30)),
    time_end: str = str(date.today() + timedelta(days=1)),
    have_not_answer: bool = True,
    have_low_score: bool = False,
) -> list[dict[str, str]]:
    """Функция для выгрузки вопросов для обработки в классе ClusterAnalysis

    Args:
        time_start (str, optional): дата, от которой нужно сортировать вопросы. По-умолчанию, 30 дней назад.
        time_end (str, optional): дата, до которой нужно сортировать вопросы. По-умолчанию, завтрашняя дата.
        have_not_answer (bool, optional): вопросы без ответа. По-умолчанию True.
        have_low_score (bool, optional): вопросы с низкой оценкой. По-умолчанию False.

    Returns:
        list[dict[str, str]]: список вопросов - словарей с ключами `text` и `date`
    """

    with Session(db.engine) as session:
        query = session.query(QuestionAnswer).filter(
            QuestionAnswer.time_created.between(time_start, time_end)
        )
        if have_not_answer and have_low_score:
            query = query.filter(
                or_(QuestionAnswer.answer == "", QuestionAnswer.score == 1)
            )
        elif have_not_answer:
            query = query.filter(QuestionAnswer.answer == "")
        elif have_low_score:
            query = query.filter(QuestionAnswer.score == 1)
        else:
            return []
        questions = (
            {"text": qa.question, "date": qa.time_created.strftime("%Y-%m-%d")}
            for qa in query
        )
        return list(questions)
