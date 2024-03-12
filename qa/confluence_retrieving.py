import logging
from atlassian import Confluence
from bs4 import BeautifulSoup
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session
from config import Config
from database import Chunk


def get_document_content_by_id(confluence: Confluence, page_id: str) -> tuple[str | None, str | None]:
    """Возвращает содержимое страницы на Confluence после предобработки с помощью PyPDF или BS4 и ссылку на страницу

    :param confluence: экземпляр Confluence
    :type confluence: Confluence
    :param page_id: ИД страницы
    :type page_id: str
    :return: содержимое страницы, ссылка на страницу
    :rtype: tuple[str | None, str | None]
    """

    page = confluence.get_page_by_id(page_id, expand='space,body.export_view')
    page_link = page['_links']['base'] + page['_links']['webui']
    page_body = page['body']['export_view']['value']
    page_download = page['_links']['base'] + \
        page['_links']['download'] if 'download' in page['_links'].keys() else ''
    try:
        if len(page_body) > 50:
            page_body = page['body']['export_view']['value']
            soup = BeautifulSoup(page_body, 'html.parser')
            page_body_text = soup.get_text(separator=' ')
            page_content = page_body_text.replace(" \n ", "")
        elif '.pdf' in page_download.lower():
            loader = PyPDFLoader(page_download.split('?')[0])
            page_content = " ".join(
                [page.page_content for page in loader.load_and_split()])
        else:
            return None, None
    except Exception as e:
        logging.error(e)
        return None, None
    return page_content, page_link


def reindex_confluence(engine: Engine, text_splitter: SentenceTransformersTokenTextSplitter):
    """Пересоздаёт векторный индекс тестов для ответов на вопросы

    :param engine: экземпляр подключения к БД
    :type engine: Engine
    :param text_splitter: экземпляр SentenceTransformersTokenTextSplitter
    :type text_splitter: SentenceTransformersTokenTextSplitter
    """

    logging.info("START CREATE INDEX")
    confluence = Confluence(url=Config.CONFLUENCE_HOST,
                            token=Config.CONFLUENCE_TOKEN)
    spaces = "(" + \
        " or ".join(
            [f"space = {space}" for space in Config.CONFLUENCE_SPACES]) + ")"
    page_ids = []
    count_start = 0
    limit = 100
    pages = confluence.cql(f"{spaces} and label != \"навигация\" order by id",
                           start=count_start, limit=limit)["results"]
    while len(pages) != 0:
        page_ids = page_ids + [page['content']['id']
                               for page in pages if 'content' in page.keys()]
        count_start += limit
        pages = confluence.cql(
            f"{spaces} and label != \"навигация\" order by id", start=count_start, limit=limit)["results"]
    documents = []
    for page_id in page_ids:
        page_content, page_link = get_document_content_by_id(
            confluence, page_id)
        if page_content is None:
            continue
        documents.append(Document(
            page_content=page_content, metadata={"page_link": page_link}
        ))
    all_splits = text_splitter.split_documents(documents)
    with Session(engine) as session:
        session.query(Chunk).delete()
        for chunk in all_splits:
            session.add(Chunk(
                confluence_url=chunk.metadata["page_link"],
                text=chunk.page_content,
                embedding=text_splitter._model.encode(chunk.page_content)
            ))
        session.commit()
    logging.info("INDEX CREATED")


def get_chunk(engine: Engine, model: SentenceTransformer, question: str) -> Chunk | None:
    """Возвращает ближайший к вопросу фрагмент документа Chunk из векторной базы данных

    :param engine: экземпляр подключения к БД
    :type engine: Engine
    :param model: модель SentenceTransformer
    :type model: SentenceTransformer
    :param question: вопрос пользователя
    :type question: str
    :return: экземпляр класса Chunk — фрагмент документа
    :rtype: Chunk | None
    """

    with Session(engine) as session:
        return session.scalars(select(Chunk)
                               .order_by(Chunk.embedding.cosine_distance(
                                   model.encode(question)
                               )).limit(1)).first()
