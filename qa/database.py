import logging
from pgvector.sqlalchemy import Vector
from sqlalchemy import Text, Column, DateTime, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
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


# migrations
if __name__ == "__main__":
    import time
    from sqlalchemy import create_engine
    from config import Config
    while True:
        try:
            engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, echo=True)
            with Session(engine) as session:
                session.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
                session.commit()
            Base.metadata.create_all(engine)
            break
        except Exception as e:
            logging.error(e)
            time.sleep(2)
