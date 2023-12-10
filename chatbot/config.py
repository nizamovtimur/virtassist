from os import environ
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")


class Config:
    SQLALCHEMY_DATABASE_URI = f"postgresql://{environ.get('POSTGRES_USER')}:{environ.get('POSTGRES_PASSWORD')}@{environ.get('POSTGRES_HOST')}/{environ.get('POSTGRES_DB')}"
    VK_ACCESS_GROUP_TOKEN = environ.get('VK_ACCESS_GROUP_TOKEN')
    VK_SUPERUSER_ID = [int(id) for id in environ.get('VK_SUPERUSER_ID').split()]
    TG_ACCESS_TOKEN = environ.get('TG_ACCESS_TOKEN')
    TG_SUPERUSER_ID = [int(id) for id in environ.get('TG_SUPERUSER_ID').split()]
    QA_HOST = environ.get('QA_HOST')
