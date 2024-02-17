from atlassian import Confluence
from bs4 import BeautifulSoup
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from config import Config
from database import Chunk


def get_document_content_by_id(confluence: Confluence, page_id: str) -> str | None:
    page = confluence.get_page_by_id(page_id, expand='space,body.export_view')
    page_body = page['body']['export_view']['value']
    page_download = page['_links']['base'] + page['_links']['download'] if 'download' in page['_links'].keys() else ''
    try:
        if len(page_body) > 50:
            page_body = page['body']['export_view']['value']
            soup = BeautifulSoup(page_body, 'html.parser')
            page_body_text = soup.get_text(separator=' ')
            content = page_body_text.replace(" \n ", "")
        elif '.pdf' in page_download.lower():
            loader = PyPDFLoader(page_download.split('?')[0])
            content = " ".join([page.page_content for page in loader.load_and_split()])
        else:
            return None
    except:
        return None
    return content


def reindex_confluence(engine: Engine):
    print("START CREATE INDEX")
    confluence = Confluence(url=Config.CONFLUENCE_HOST, token=Config.CONFLUENCE_TOKEN)
    spaces = "(" + " or ".join([f"space = {space}" for space in Config.CONFLUENCE_SPACES]) + ")"
    page_ids = []
    count_start = 0
    limit = 100
    pages = confluence.cql(f"{spaces} and label != \"навигация\" order by id", start=count_start, limit=limit)["results"]
    while len(pages) != 0:
        page_ids = page_ids + [page['content']['id'] for page in pages if 'content' in page.keys()]
        count_start += limit
        pages = confluence.cql(f"{spaces} and label != \"навигация\" order by id", start=count_start, limit=limit)["results"]
        
    documents = []
    for page_id in page_ids:
        page_content = get_document_content_by_id(confluence, page_id)
        if page_content is None:
            continue
        documents.append(Document(
            page_content=page_content, metadata={"page_id": int(page_id)}
        ))
    
    text_splitter = SentenceTransformersTokenTextSplitter(model_name="saved_models/rubert-tiny2-wikiutmn")   
    all_splits = text_splitter.split_documents(documents)
    
    with Session(engine) as session:
        session.query(Chunk).delete()
        for chunk in all_splits:
            session.add(Chunk(
                confluence_id=chunk.metadata["page_id"],
                text=chunk.page_content,
                embedding=text_splitter._model.encode(chunk.page_content)
            ))
        session.commit()
    print("INDEX CREATED")
