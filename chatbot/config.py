from os import environ
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")


class Config:
    SQLALCHEMY_DATABASE_URI = f"postgresql://{environ.get('POSTGRES_USER')}:{environ.get('POSTGRES_PASSWORD')}@{environ.get('POSTGRES_HOST')}/{environ.get('POSTGRES_DB')}"
    VK_ACCESS_GROUP_TOKEN = environ.get('VK_ACCESS_GROUP_TOKEN')
    VK_SUPERUSER_ID = [(int(id) for id in environ.get('VK_SUPERUSER_ID').split(
    )) if environ.get('VK_SUPERUSER_ID') is not None else 0]
    TG_ACCESS_TOKEN = environ.get('TG_ACCESS_TOKEN')
    TG_SUPERUSER_ID = [(int(id) for id in environ.get('TG_SUPERUSER_ID').split(
    )) if environ.get('TG_SUPERUSER_ID') is not None else 0]
    QA_HOST = environ.get('QA_HOST')
    CONFLUENCE_TOKEN = environ.get('CONFLUENCE_TOKEN')
    CONFLUENCE_HOST = environ.get('CONFLUENCE_HOST')
    CONFLUENCE_SPACES = environ.get('CONFLUENCE_SPACES').split(
    ) if environ.get('CONFLUENCE_SPACES') is not None else []
    PRIVACY_POLICY_URL = environ.get('PRIVACY_POLICY_URL')
