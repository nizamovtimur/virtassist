FROM python:3.10.0-slim-buster

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt-get -y install curl cron

RUN crontab -l | { cat; echo "0 6,18 * * * curl -X POST http://localhost/reindex/"; } | crontab -

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . /usr/src/app/

RUN python save_models.py