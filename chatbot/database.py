from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Text, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship


class Base(DeclarativeBase):
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vk_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True)
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True)
    is_subscribed: Mapped[bool] = mapped_column()

    question_answers: Mapped[List["QuestionAnswer"]] = relationship(back_populates="user", cascade="all, delete-orphan", order_by="desc(QuestionAnswer.time_created)")
    
    
class QuestionAnswer(Base):
    __tablename__ = "question_answer"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(Text())
    answer: Mapped[Optional[str]] = mapped_column(Text())
    confluence_url: Mapped[Optional[str]] = mapped_column(Text(), index=True)
    score: Mapped[Optional[int]] = mapped_column()
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))

    user: Mapped["User"] = relationship(back_populates="question_answers")


# migrations
if __name__ == "__main__":
    import time
    from sqlalchemy import create_engine
    from config import Config
    while True:
        try:
            engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, echo=True)
            Base.metadata.create_all(engine)
            break
        except Exception as e:
            print(e)
            time.sleep(2)


def add_user(engine, vk_id: int|None = None, telegram_id: int|None = None) -> tuple[bool, int]:
    with Session(engine) as session:
        if vk_id is not None:
            user = session.scalar(select(User).where(User.vk_id == vk_id))
        elif telegram_id is not None:
            user = session.scalar(select(User).where(User.telegram_id == telegram_id))
        else:
            raise Exception("vk_id and telegram_id can't be None at the same time")
        if user is None:
            user = User(vk_id=vk_id, telegram_id=telegram_id, is_subscribed=True)
            session.add(user)
            session.commit()
            return True, user.id
        return False, user.id

            
def get_user_id(engine, vk_id: int|None = None, telegram_id: int|None = None) -> int | None:
    with Session(engine) as session:
        if vk_id is not None:
            user = session.scalar(select(User).where(User.vk_id == vk_id))
        elif telegram_id is not None:
            user = session.scalar(select(User).where(User.telegram_id == telegram_id))
        else:
            raise Exception("vk_id and telegram_id can't be None at the same time")
        if user is None:
            return None
        return user.id
        

def subscribe_user(engine, user_id: int) -> bool:
    with Session(engine) as session:
        user = session.scalars(select(User).where(User.id == user_id)).first()
        if user is None:
            return False
        user.is_subscribed = not user.is_subscribed
        session.commit()
        return user.is_subscribed


def check_subscribing(engine, user_id: int) -> bool:
    with Session(engine) as session:
        user = session.scalars(select(User).where(User.id == user_id)).first()
        if user is None:
            return False
        return user.is_subscribed


def check_spam(engine, user_id: int) -> bool:
    with Session(engine) as session:
        user = session.scalars(select(User).where(User.id == user_id)).first()
        if user is None:
            return False
        if len(user.question_answers) > 3:
            return datetime.now(timezone.utc).replace(tzinfo=None) - user.question_answers[2].time_created.replace(tzinfo=None) < timedelta(minutes=1)
        return False


def add_question_answer(engine, question: str, answer: str, confluence_url: str | None, user_id: int) -> int:
    with Session(engine) as session:
        question_answer = QuestionAnswer(
            question=question,
            answer=answer,
            confluence_url=confluence_url,
            user_id=user_id
        )
        session.add(question_answer)
        session.flush()
        session.refresh(question_answer)
        session.commit()
        if question_answer.id is None:
            return 0
        return question_answer.id


def rate_answer(engine, question_answer_id: int, score: int) -> bool:
    with Session(engine) as session:
        question_answer = session.scalars(select(QuestionAnswer).where(QuestionAnswer.id == question_answer_id)).first()
        if question_answer is None:
            return False
        question_answer.score = score
        session.commit()
        return True
