from contextlib import redirect_stderr
import io
import logging
from aiohttp import web
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from config import Config
from database import Chunk
from gigachat_prompting import get_answer
from confluence_retrieving import get_chunk, reindex_confluence


routes = web.RouteTableDef()
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
text_splitter = SentenceTransformersTokenTextSplitter(
    model_name="saved_models/rubert-tiny2-wikiutmn")


@routes.post('/qa/')
async def qa(request: web.Request) -> web.Response:
    """Возвращает ответ на вопрос пользователя и ссылку на источник

    Args:
        request (web.Request): запрос, содержащий `question`

    Returns:
        web.Response: ответ
    """

    question = (await request.json())['question']
    chunk = get_chunk(engine, text_splitter._model, question)
    if chunk is None:
        return web.Response(text="Chunk not found", status=404)
    alt_stream = io.StringIO()
    with redirect_stderr(alt_stream):
        answer = get_answer(chunk.text, question)
    warnings = alt_stream.getvalue()
    if len(warnings) > 0:
        logging.warning(warnings)
    if "stopped" in warnings or "ответ не найден" in answer.lower():
        return web.Response(text="Answer not found", status=404)
    return web.json_response({
        "answer": answer,
        "confluence_url": chunk.confluence_url
    })


@routes.post('/reindex/')
async def reindex(request: web.Request) -> web.Response:
    """Пересоздаёт векторный индекс текстов для ответов на вопросы

    Args:
        request (web.Request): запрос

    Returns:
        web.Response: ответ
    """

    try:
        reindex_confluence(engine, text_splitter)
        return web.Response(status=200)
    except Exception as e:
        return web.Response(text=str(e), status=500)


if __name__ == "__main__":
    with Session(engine) as session:
        questions = session.scalars(select(Chunk)).first()
        if questions is None:
            reindex_confluence(engine, text_splitter)
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app)
