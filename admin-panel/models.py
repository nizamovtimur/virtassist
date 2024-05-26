from typing import Optional, List
from datetime import date, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Text, func, or_
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from cluster_analysis import mark_of_question
from config import app


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
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(QuestionAnswer.time_created)",
    )


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


def get_questions_for_clusters(
    time_start: str = str(date.today() - timedelta(days=30)),
    time_end: str = str(date.today() + timedelta(days=1)),
    have_not_answer: bool = True,
    have_low_score: bool = False,
    have_high_score: bool = False,
    have_not_score: bool = False,
) -> list[dict[str, str | mark_of_question]]:
    """Функция для выгрузки вопросов для обработки в классе ClusterAnalysis

    Args:
        time_start (str, optional): дата, от которой нужно сортировать вопросы. По-умолчанию, 30 дней назад.
        time_end (str, optional): дата, до которой нужно сортировать вопросы. По-умолчанию, завтрашняя дата.
        have_not_answer (bool, optional): вопросы без ответа. По-умолчанию True.
        have_low_score (bool, optional): вопросы с низкой оценкой. По-умолчанию False.
        have_high_score (bool, optional): вопросы с высокой оценкой False.
        have_not_score (bool, optional): вопросы без оценки False.

    Returns:
        list[dict[str, str]]: список вопросов - словарей с ключами `text` и `date`
    """

    with Session(db.engine) as session:
        query = session.query(QuestionAnswer).filter(
            QuestionAnswer.time_created.between(time_start, time_end)
        )
        """
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
        """
        questions = []
        if have_not_answer:
            for qa in query.filter(QuestionAnswer.answer == ""):
                questions.append(
                    {
                        "text": qa.question,
                        "date": qa.time_created.strftime("%Y-%m-%d"),
                        "type": mark_of_question.have_not_answer,
                    }
                )
        if have_low_score:
            for qa in query.filter(QuestionAnswer.score == 1):
                questions.append(
                    {
                        "text": qa.question,
                        "date": qa.time_created.strftime("%Y-%m-%d"),
                        "type": mark_of_question.have_low_score,
                    }
                )
        if have_high_score:
            for qa in query.filter(QuestionAnswer.score == 5):
                questions.append(
                    {
                        "text": qa.question,
                        "date": qa.time_created.strftime("%Y-%m-%d"),
                        "type": mark_of_question.have_low_score,
                    }
                )
        if have_not_score:
            for qa in query.filter(QuestionAnswer.score == None):
                questions.append(
                    {
                        "text": qa.question,
                        "date": qa.time_created.strftime("%Y-%m-%d"),
                        "type": mark_of_question.have_low_score,
                    }
                )
        return questions
