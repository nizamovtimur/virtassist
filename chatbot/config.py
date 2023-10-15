from os import environ
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")


class Config:
    SQLALCHEMY_DATABASE_URI = f"postgresql://{environ.get('POSTGRES_USER')}:{environ.get('POSTGRES_PASSWORD')}@{environ.get('POSTGRES_HOST')}/{environ.get('POSTGRES_DB')}"
    ACCESS_GROUP_TOKEN = environ.get('ACCESS_GROUP_TOKEN')
    SUPERUSER_VK_ID = int(environ.get('SUPERUSER_VK_ID'))
