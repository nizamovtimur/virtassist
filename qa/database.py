from pgvector.sqlalchemy import Vector
from sqlalchemy import Text, Column, DateTime, func
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

Base = declarative_base()


class Chunk(Base):
    """Фрагмент документа из вики-системы

    Args:
        confluence_url (str): ссылка на источник
        text (str): текст фрагмента
        embedding (Vector): векторное представление текста фрагмента размерностью 1024
        created_at (datetime): время создания модели
        updated_at (datetime): время обновления модели
    """

    __tablename__ = "chunk"

    id: Mapped[int] = mapped_column(primary_key=True)
    confluence_url: Mapped[str] = mapped_column(Text(), index=True)
    text: Mapped[str] = mapped_column(Text())
    embedding: Mapped[Vector] = mapped_column(Vector(1024))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
