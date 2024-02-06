import bs4


def make_markup_by_confluence(confluence, space):
    question_types = {}
    for i in confluence.get_all_pages_from_space(space, expand='ancestors'):
        if len(i['ancestors']) == 1: 
            question_types[i['title']] = i['id']
    return question_types


def parse_confluence_by_page_id(confluence, id) -> list | str:
    subtypes = confluence.cql(f"parent={id}")['results']
    if len(subtypes): 
        return subtypes
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
    