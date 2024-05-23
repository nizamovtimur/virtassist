from os import environ
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

load_dotenv(dotenv_path="../.env")
database_url = f"postgresql://{environ.get('POSTGRES_USER')}:{environ.get('POSTGRES_PASSWORD')}@{environ.get('POSTGRES_HOST')}/{environ.get('POSTGRES_DB')}"
engine = create_engine(database_url)
with Session(engine) as session:
    session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    session.commit()
