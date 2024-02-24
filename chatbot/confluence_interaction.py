﻿from atlassian import Confluence 
import bs4
from functools import cache


@cache
def make_markup_by_confluence(confluence: Confluence, space: str) -> list:
    homepage_id = confluence.get_space(space, expand='homepage')["homepage"]["id"]
    pages = confluence.cql(f"parent={homepage_id} and label=\"справка\"")['results']
    return pages


@cache
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


def cache_confluence_tree(confluence: Confluence, space: str):
        tree = make_markup_by_confluence(confluence, space)
        for i in tree:
            parse = parse_confluence_by_page_id(confluence, i['content']['id'])
            if type(parse) == list:
                for l in parse:
                    parse_confluence_by_page_id(confluence, l['content']['id'])