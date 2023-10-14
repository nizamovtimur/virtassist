from typing import Optional, List
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    dialog_iteration: Mapped[int] = mapped_column()
    is_subscribed: Mapped[int] = mapped_column()
    experience: Mapped[Optional[str]] = mapped_column(Text())
    fantasies: Mapped[Optional[str]] = mapped_column(Text())

    questions: Mapped[List["Question"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, is_subscribed={self.is_subscribed!r})"


class Question(Base):
    __tablename__ = "question"
    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[Optional[str]] = mapped_column(Text())
    answer: Mapped[Optional[str]] = mapped_column(Text())
    department: Mapped[Optional[str]] = mapped_column(Text())
    score: Mapped[Optional[str]] = mapped_column(Text())
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))

    user: Mapped["User"] = relationship(back_populates="questions")

    def __repr__(self) -> str:
        return (f"Question(question={self.question!r}, answer={self.answer!r}, "
                f"department={self.department!r}, score={self.score!r})")


# migrations
if __name__ == "__main__":
    from sqlalchemy import create_engine
    from config import Config
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, echo=True)
    Base.metadata.create_all(engine)
