import logging
from atlassian import Confluence
from bs4 import BeautifulSoup
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import TextSplitter
from sentence_transformers import SentenceTransformer
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session
from config import Config
from database import Chunk


def get_document_content_by_id(
    confluence: Confluence, page_id: str
) -> tuple[str | None, str | None]:
    """Возвращает содержимое страницы на Confluence
    после предобработки с помощью PyPDF или BS4 и ссылку на страницу

    Args:
        confluence (Confluence): экземпляр Confluence
        page_id (str): ID страницы

    Returns:
        tuple[str | None, str | None]: содержимое страницы, ссылка на страницу
    """

    page = confluence.get_page_by_id(page_id, expand="space,body.export_view")
    page_link = page["_links"]["base"] + page["_links"]["webui"]
    page_body = page["body"]["export_view"]["value"]
    page_download = (
        page["_links"]["base"] + page["_links"]["download"]
        if "download" in page["_links"].keys()
        else ""
    )
    try:
        if len(page_body) > 50:
            page_body = page["body"]["export_view"]["value"]
            soup = BeautifulSoup(page_body, "html.parser")
            page_body_text = soup.get_text(separator=" ")
            page_content = page_body_text.replace(" \n ", "")
        elif ".pdf" in page_download.lower():
            loader = PyPDFLoader(page_download.split("?")[0])
            page_content = " ".join(
                [page.page_content for page in loader.load_and_split()]
            )
        else:
            return None, None
    except Exception as e:
        logging.error(e)
        return None, None
    return page_content, page_link


def reindex_confluence(
    engine: Engine, text_splitter: TextSplitter, encoder_model: SentenceTransformer
):
    """Пересоздаёт векторный индекс текстов для ответов на вопросы.
    При этом обрабатываются страницы, не имеющие вложенных страниц.

    Args:
        engine (Engine): экземпляр подключения к БД
        text_splitter (TextSplitter): разделитель текста на фрагменты
        encoder_model (SentenceTransformer): модель получения векторных представлений Sentence Transformer
    """

    logging.warning("START CREATE INDEX")
    confluence = Confluence(url=Config.CONFLUENCE_HOST, token=Config.CONFLUENCE_TOKEN)
    spaces = (
        "("
        + " or ".join([f"space = {space}" for space in Config.CONFLUENCE_SPACES])
        + ")"
    )
    page_ids = []
    count_start = 0
    limit = 100
    while True:
        query = f"{spaces} order by id"
        pages = confluence.cql(query, start=count_start, limit=limit)["results"]
        if len(pages) == 0:
            break
        page_ids += [
            page["content"]["id"] for page in pages if "content" in page.keys()
        ]
        count_start += limit
    documents = []
    for page_id in page_ids:
        children = confluence.cql(f"parent={page_id}")["results"]
        if len(children) > 0:
            continue
        page_content, page_link = get_document_content_by_id(confluence, page_id)
        if page_content is None:
            continue
        documents.append(
            Document(page_content=page_content, metadata={"page_link": page_link})
        )
    all_splits = text_splitter.split_documents(documents)
    with Session(engine) as session:
        session.query(Chunk).delete()
        for chunk in all_splits:
            session.add(
                Chunk(
                    confluence_url=chunk.metadata["page_link"],
                    text=chunk.page_content,
                    embedding=encoder_model.encode(chunk.page_content),
                )
            )
        session.commit()
    logging.warning("INDEX CREATED")


def get_chunk(
    engine: Engine, encoder_model: SentenceTransformer, question: str
) -> Chunk | None:
    """Возвращает ближайший к вопросу фрагмент документа Chunk из векторной базы данных

    Args:
        engine (Engine): экземпляр подключения к БД
        encoder_model (SentenceTransformer): модель получения векторных представлений SentenceTransformer
        question (str): вопрос пользователя

    Returns:
        Chunk | None: экземпляр класса Chunk — фрагмент документа
    """

    with Session(engine) as session:
        return session.scalars(
            select(Chunk)
            .order_by(Chunk.embedding.cosine_distance(encoder_model.encode(question)))
            .limit(1)
        ).first()
