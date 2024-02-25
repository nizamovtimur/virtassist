from atlassian import Confluence 
import bs4
from cachetools import cached, TTLCache

@cached(cache=TTLCache(maxsize=100, ttl=3600))
def make_markup_by_confluence(confluence: Confluence, space: str) -> list:
    homepage_id = confluence.get_space(space, expand='homepage')["homepage"]["id"]
    pages = confluence.cql(f"parent={homepage_id} and label=\"справка\"")['results']
    return pages


@cached(cache=TTLCache(maxsize=100, ttl=3600))
def parse_confluence_by_page_id(confluence: Confluence, id: int | str) -> list | str:
    pages = confluence.cql(f"parent={id} and label=\"справка\"")['results']
    if len(pages): 
        return pages
    else: 
        page = confluence.get_page_by_id(int(id), expand='body.storage')
        page_link = page['_links']['base'] + page['_links']['webui']
        page_body = page['body']['storage']['value']
        soup = bs4.BeautifulSoup(page_body, 'html.parser')
        text = ''
        for i in soup.find_all('strong'): i.unwrap()
        for i in soup.select('br'): i.replace_with('\n')
        for i in soup.find_all():
            if i.find('ac:parameter'): i.decompose()
        for i in soup.find_all(['p', 'ul']):
            text += i.get_text() + '\n\n'
        if text != '': return text 
        else: return f'Информация находится по ссылке: {page_link}'