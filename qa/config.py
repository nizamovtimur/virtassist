from os import environ
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")


class Config:
    HUGGINGFACE_TOKEN = environ.get('HUGGINGFACE_TOKEN')
    GIGACHAT_TOKEN = environ.get('GIGACHAT_TOKEN')
    CONFLUENCE_TOKEN = environ.get('CONFLUENCE_TOKEN')
