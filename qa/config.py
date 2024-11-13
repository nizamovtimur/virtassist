from os import environ
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")


class Config:
    """Класс с переменными окружения"""

    GIGACHAT_TOKEN = environ.get("GIGACHAT_TOKEN")
    GIGACHAT_MODEL = environ.get("GIGACHAT_MODEL")
    GIGACHAT_SCOPE = environ.get("GIGACHAT_SCOPE")
    CONFLUENCE_TOKEN = environ.get("CONFLUENCE_TOKEN")
    CONFLUENCE_HOST = environ.get("CONFLUENCE_HOST")
    CONFLUENCE_SPACES = environ.get("CONFLUENCE_SPACES").split()
    SQLALCHEMY_DATABASE_URI = f"postgresql://{environ.get('POSTGRES_USER')}:{environ.get('POSTGRES_PASSWORD')}@{environ.get('POSTGRES_HOST')}/{environ.get('POSTGRES_DB')}"
