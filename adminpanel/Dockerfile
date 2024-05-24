FROM python:3.10.0-slim-buster

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY ./save_nltk.py .
RUN python save_nltk.py
RUN python -m spacy download ru_core_news_sm

COPY . /app
WORKDIR /app
