from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Engine,
    ForeignKey,
    Text,
    func,
    select,
    and_,
)
from sqlalchemy.orm import (
    Mapped,
    Session,
    declarative_base,
    mapped_column,
    relationship,
)

Base = declarative_base()


class User(Base):
    """Пользователь чат-бота

    Args:
        id (int): id пользователя
        vk_id (int | None): id пользователя ВКонтакте
        telegram_id (int | None): id пользователя Telegram
        is_subscribed (bool): состояние подписки пользователя
        created_at (datetime): время создания модели
        updated_at (datetime): время обновления модели
    """

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vk_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True)
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True)
    is_subscribed: Mapped[bool] = mapped_column()

    question_answers: Mapped[List["QuestionAnswer"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(QuestionAnswer.created_at)",
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class QuestionAnswer(Base):
    """Вопрос пользователя с ответом на него

    Args:
        id (int): id ответа
        question (str): вопрос пользователя
        answer (str | None): ответ на вопрос пользователя
        confluence_url (str | None): ссылка на страницу в вики-системе, содержащую ответ
        score (int | None): оценка пользователем ответа
        user_id (int): id пользователя, задавшего вопрос
        created_at (datetime): время создания модели
        updated_at (datetime): время обновления модели
    """

    __tablename__ = "question_answer"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(Text())
    answer: Mapped[Optional[str]] = mapped_column(Text())
    confluence_url: Mapped[Optional[str]] = mapped_column(Text(), index=True)
    score: Mapped[Optional[int]] = mapped_column()
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))

    user: Mapped["User"] = relationship(back_populates="question_answers")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


def add_user(
    engine: Engine, vk_id: int | None = None, telegram_id: int | None = None
) -> tuple[bool, int]:
    """Функция добавления в БД пользователя виртуального помощника

    Args:
        engine (Engine): подключение к БД
        vk_id (int | None): id пользователя ВКонтакте
        telegram_id (int | None): id пользователя Telegram

    Raises:
        TypeError: vk_id и telegram_id не могут быть None в одно время

    Returns:
        tuple[bool, int]: добавился пользователь или нет, какой у него id в БД
    """

    with Session(engine) as session:
        if vk_id is not None:
            user = session.scalar(select(User).where(User.vk_id == vk_id))
        elif telegram_id is not None:
            user = session.scalar(select(User).where(User.telegram_id == telegram_id))
        else:
            raise TypeError("vk_id and telegram_id can't be None at the same time")
        if user is None:
            user = User(vk_id=vk_id, telegram_id=telegram_id, is_subscribed=True)
            session.add(user)
            session.commit()
            return True, user.id
        return False, user.id


def get_user_id(
    engine: Engine, vk_id: int | None = None, telegram_id: int | None = None
) -> int | None:
    """Функция получения из БД пользователя

    Args:
        engine (Engine): подключение к БД
        vk_id (int | None): id пользователя ВКонтакте
        telegram_id (int | None): id пользователя Telegram

    Raises:
        TypeError: vk_id и telegram_id не могут быть None в одно время

    Returns:
        int | None: id пользователя или None
    """

    with Session(engine) as session:
        if vk_id is not None:
            user = session.scalar(select(User).where(User.vk_id == vk_id))
        elif telegram_id is not None:
            user = session.scalar(select(User).where(User.telegram_id == telegram_id))
        else:
            raise TypeError("vk_id and telegram_id can't be None at the same time")
        if user is None:
            return None
        return user.id


def subscribe_user(engine: Engine, user_id: int) -> bool:
    """Функция оформления подписки пользователя на рассылку

    Args:
        engine (Engine): подключение к БД
        user_id (int): id пользователя

    Returns:
        bool: подписан пользователь или нет
    """

    with Session(engine) as session:
        user = session.scalars(select(User).where(User.id == user_id)).first()
        if user is None:
            return False
        user.is_subscribed = not user.is_subscribed
        session.commit()
        return user.is_subscribed


def check_subscribing(engine: Engine, user_id: int) -> bool:
    """Функция проверки подписки пользователя на рассылку

    Args:
        engine (Engine): подключение к БД
        user_id (int): id пользователя

    Returns:
        bool: подписан пользователь или нет
    """

    with Session(engine) as session:
        user = session.scalars(select(User).where(User.id == user_id)).first()
        if user is None:
            return False
        return user.is_subscribed


def check_spam(engine: Engine, user_id: int) -> bool:
    """Функция проверки на спам

    Args:
        engine (Engine): подключение к БД
        user_id (int): id пользователя

    Returns:
        bool: пользователь задал три вопроса за последнюю минуту
    """

    with Session(engine) as session:
        user = session.scalars(select(User).where(User.id == user_id)).first()
        if user is None:
            return False
        if len(user.question_answers) > 3:
            minute_ago = datetime.now() - timedelta(minutes=1)
            third_message_date = user.question_answers[2].created_at
            return minute_ago < third_message_date.replace(tzinfo=None)
        return False


def add_question_answer(
    engine: Engine, question: str, answer: str, confluence_url: str | None, user_id: int
) -> int:
    """Функция добавления в БД вопроса пользователя с ответом на него

    Args:
        engine (Engine): подключение к БД
        question (str): вопрос пользователя
        answer (str): ответ на вопрос пользователя
        confluence_url (str | None): ссылка на страницу в вики-системе, содержащую ответ
        user_id (int): id пользователя

    Returns:
        int: id вопроса с ответом на него
    """

    with Session(engine) as session:
        question_answer = QuestionAnswer(
            question=question,
            answer=answer,
            confluence_url=confluence_url,
            user_id=user_id,
        )
        session.add(question_answer)
        session.flush()
        session.refresh(question_answer)
        session.commit()
        if question_answer.id is None:
            return 0
        return question_answer.id


def rate_answer(engine: Engine, question_answer_id: int, score: int) -> bool:
    """Функция оценивания ответа на вопрос

    Args:
        engine (Engine): подключение к БД
        question_answer_id (int): id вопроса с ответом
        score (int): оценка ответа

    Returns:
        bool: удалось добавить в БД оценку ответа или нет
    """

    with Session(engine) as session:
        question_answer = session.scalars(
            select(QuestionAnswer).where(QuestionAnswer.id == question_answer_id)
        ).first()
        if question_answer is None:
            return False
        question_answer.score = score
        session.commit()
        return True


def get_subscribed_users(engine: Engine) -> tuple[list[int | None], list[int | None]]:
    """Функция для получения подписанных на рассылки пользователей

    Args:
        engine (Engine): подключение к БД

    Returns:
        tuple[list[int], list[int]]: кортеж списков с id пользователей VK и Telegram
    """
    with Session(engine) as session:
        vk_users = [
            user.vk_id
            for user in session.execute(
                select(User).where(and_(User.vk_id != None, User.is_subscribed))
            ).scalars()
        ]
        tg_users = [
            user.telegram_id
            for user in session.execute(
                select(User).where(and_(User.telegram_id != None, User.is_subscribed))
            ).scalars()
        ]
    return vk_users, tg_users
