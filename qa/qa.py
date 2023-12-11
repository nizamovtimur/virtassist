from aiohttp import web
from atlassian import Confluence
from bs4 import BeautifulSoup
from langchain.document_loaders import PyPDFLoader
from langchain.llms import GigaChat
from langchain.prompts import PromptTemplate
import spacy
from config import Config

needed_pos = ['NOUN', 'NUM', 'PROPN', 'VERB', 'X']
routes = web.RouteTableDef()
nlp = spacy.load("ru_core_news_sm")
confluence = Confluence(url=Config.CONFLUENCE_HOST, token=Config.CONFLUENCE_TOKEN)
giga = GigaChat(credentials=Config.GIGACHAT_TOKEN, verify_ssl_certs=False)
prompt_template = """
Ты цифровой помощник студента ТюмГУ, помогаешь отвечать на вопросы. Извлеки ответ на вопрос из документа. 

Документ:
{context}

Вопрос: {question}
"""
prompt = PromptTemplate.from_template(prompt_template)
giga_chain = prompt | giga


def get_cql_query(spaces, question):
    words = [(token.lemma_, token.pos_) for token in nlp(question.lower()) if not token.is_stop and
             token.pos_ in needed_pos and len(token.text) > 2]
    spaces = " or ".join([f"space = {space}" for space in spaces])
    words_with_verbs = " and ".join([f"text ~ '{word[0]}*'" for word in words])
    words_without_verbs = " and ".join([f"text ~ '{word[0]}*'" for word in words if word[1] != 'VERB'])
    return "(" + spaces + ") and (" + words_with_verbs + ")", "(" + spaces + ") and (" + words_without_verbs + ")"


def get_answer_gigachat(question: str):
    cql_query = get_cql_query(spaces=Config.CONFLUENCE_SPACES, question=question)
    if "()" in cql_query[0]:
        return ""
    results = confluence.cql(cql_query[0], start=0, limit=1)['results']
    if len(results) == 0:
        results = confluence.cql(cql_query[1], start=0, limit=1)['results']
        if len(results) == 0:
            return ""

    page_id = results[0]['content']['id']
    page = confluence.get_page_by_id(page_id, expand='space,body.export_view')
    page_title, page_link = page['title'], page['_links']['base'] + page['_links']['webui']
    page_body = page['body']['export_view']['value']
    page_download = page['_links']['base'] + page['_links']['download'] if 'download' in page['_links'].keys() else ''

    if len(page_body) > 50:
        page_body = page['body']['export_view']['value']
        soup = BeautifulSoup(page_body, 'html.parser')
        page_body_text = soup.get_text(separator=' ')
        context = page_body_text.replace(" \n ", "")
    elif '.pdf' in page_download.lower():
        loader = PyPDFLoader(page_download.split('?')[0])
        context = " ".join([page.page_content for page in loader.load_and_split()])
    else:
        return ""

    query = {"context": " ".join(context.split()[:4000]),
             "question": question}
    try:
        answer = giga_chain.invoke(query).strip()
    except:
        return ""
    return f"{answer}\n\nПодробнее: {page_link}"


@routes.post('/')
async def main(request):
    question = (await request.json())['question']
    return web.Response(text=get_answer_gigachat(question))


if __name__ == "__main__":
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app)
