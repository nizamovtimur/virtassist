from os import environ
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv(dotenv_path="../.env")

openchat = ChatOpenAI(
    model="openchat_3.5",
    openai_api_key="EMPTY",
    openai_api_base=environ.get('OPENCHAT_HOST'),
    temperature=0.7,
)

while 1:
    prompt = input("Введите запрос: ")
    print("\n---------------------------\n")
    print(openchat.invoke((
    "human",
    prompt
    )).content)
    print("\n===========================\n")
