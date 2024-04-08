from os import environ
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")


class Config:
    """Класс с переменными окружения
    """

    SQLALCHEMY_DATABASE_URI = f"postgresql://{environ.get('POSTGRES_USER')}:{environ.get('POSTGRES_PASSWORD')}@{environ.get('POSTGRES_HOST')}/{environ.get('POSTGRES_DB')}"
    VK_ACCESS_GROUP_TOKEN = environ.get('VK_ACCESS_GROUP_TOKEN')
    TG_ACCESS_TOKEN = environ.get('TG_ACCESS_TOKEN')
    QA_HOST = environ.get('QA_HOST')
    CONFLUENCE_TOKEN = environ.get('CONFLUENCE_TOKEN')
    CONFLUENCE_HOST = environ.get('CONFLUENCE_HOST')
    CONFLUENCE_SPACES = environ.get('CONFLUENCE_SPACES').split(
    ) if environ.get('CONFLUENCE_SPACES') is not None else []
