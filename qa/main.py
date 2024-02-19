from aiohttp import web
from langchain.prompts import PromptTemplate
from langchain_community.llms import GigaChat
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from config import Config
from database import Chunk
from reindex_confluence import reindex_confluence


routes = web.RouteTableDef()
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
sbert_model = SentenceTransformer("saved_models/rubert-tiny2-wikiutmn")
giga = GigaChat(credentials=Config.GIGACHAT_TOKEN, verify_ssl_certs=False)
prompt_template = """
Используй следующий текст в тройных кавычках, чтобы кратко ответить на вопрос студента в конце. 
Не изменяй и не убирай ссылки, адреса и телефоны. Если ты не можешь найти ответ, напиши, что ответ не найден.
Ответ не должен превышать 100 слов.

\"\"\"
{context}
\"\"\"

Вопрос: {question}
"""
prompt = PromptTemplate.from_template(prompt_template)
giga_chain = prompt | giga


# TODO: предусмотреть порог бреда
def get_chunk(question: str) -> Chunk | None:
    with Session(engine) as session:
        return session.scalars(select(Chunk)
                        .order_by(Chunk.embedding.cosine_distance(
                            sbert_model.encode(question)
                            )).limit(1)).first()


def get_answer_gigachat(context: str, question: str) -> str:
    query = {"context": context,
             "question": question}
    try:
        return giga_chain.invoke(query).replace('"""', '').strip()
    except:
        return ""


@routes.post('/qa/')
async def qa(request):
    question = (await request.json())['question']
    chunk = get_chunk(question)
    if chunk is None:
        return web.Response(text="Chunk not found", status=404)
    return web.json_response({
        "answer": get_answer_gigachat(chunk.text, question),
        "confluence_url": chunk.confluence_url
    })


@routes.post('/reindex/')
async def reindex(request):
    try:
        reindex_confluence(engine=engine)
        return web.Response(status=200)
    except Exception as e:
        return web.Response(text=str(e), status=500) 


if __name__ == "__main__":
    with Session(engine) as session:
        questions = session.scalars(select(Chunk)).first()
        if questions is None:
            reindex_confluence(engine=engine)
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app)
