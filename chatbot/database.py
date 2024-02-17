from typing import Optional, List
from sqlalchemy import ForeignKey, BigInteger, Text, Column, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    vk_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True)
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True)
    is_subscribed: Mapped[bool] = mapped_column()

    question_answers: Mapped[List["QuestionAnswer"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    
    
class QuestionAnswer(Base):
    __tablename__ = "question_answer"
    id: Mapped[int] = mapped_column(primary_key=True)
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
