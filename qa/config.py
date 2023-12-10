from os import environ
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")


class Config:
    GIGACHAT_TOKEN = environ.get('GIGACHAT_TOKEN')
    CONFLUENCE_TOKEN = environ.get('CONFLUENCE_TOKEN')
    CONFLUENCE_HOST = environ.get('CONFLUENCE_HOST')
    CONFLUENCE_SPACES = environ.get('CONFLUENCE_SPACES').split()
