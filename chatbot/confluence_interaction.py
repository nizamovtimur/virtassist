import bs4
import requests
from atlassian import Confluence
from config import Config

confluence = Confluence(
    url=Config.CONFLUENCE_HOST,
    token=Config.CONFLUENCE_TOKEN
)

class ConfluenceInteraction:
    def make_markup_by_confluence():
        question_types = {}
		if len(Config.CONFLUENCE_SPACES) != 0:
            for i in confluence.get_all_pages_from_space(Config.CONFLUENCE_SPACES[0]):
                if len(confluence.get_page_ancestors(i['id'])) == 1: 
                    question_types[i['title']] = 'type ' + str(i['id'])
        return question_types

    def parse_confluence_by_page_id(id) -> list | str:
        subtypes = requests.get(f'{Config.CONFLUENCE_HOST}/rest/api/content/search?cql=parent={id}').json()['results']
        if len(subtypes): return subtypes
        else: 
            soup = bs4.BeautifulSoup(requests.get(f'{Config.CONFLUENCE_HOST}/rest/api/content/{id}?expand=body.storage').json()['body']['storage']['value'], 'html.parser')
            text = ''
            for i in soup.find_all('strong'): i.unwrap()
            for i in soup.select('br'): i.replace_with('\n')
            for i in soup.find_all():
                if i.find('ac:parameter'): i.decompose()
            for i in soup.find_all(['p', 'ul']):
                text += i.get_text() + '\n\n'
            if text != '': return text 
            else: return f'Информация касаемо выбранного вопроса находится по ссылке: {Config.CONFLUENCE_HOST}/pages/viewpage.action?pageId={id}'