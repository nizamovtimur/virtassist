from atlassian import Confluence
import bs4
from cachetools import cached, TTLCache
from config import Config


confluence = Confluence(url=Config.CONFLUENCE_HOST,
                        token=Config.CONFLUENCE_TOKEN)
confluence_main_space = Config.CONFLUENCE_SPACES[0]


@cached(cache=TTLCache(maxsize=100, ttl=3600))
def make_markup_by_confluence() -> list:
    homepage_id = confluence.get_space(confluence_main_space,
                                       expand="homepage")["homepage"]["id"]
    pages = confluence.cql(
        f"parent={homepage_id} and label=\"справка\"")["results"]
    return pages


@cached(cache=TTLCache(maxsize=100, ttl=3600))
def parse_confluence_by_page_id(id: int | str) -> list | str:
    pages = confluence.cql(f"parent={id} and label=\"справка\"")["results"]
    if len(pages):
        return pages
    else:
        page = confluence.get_page_by_id(int(id), expand="body.storage")
        page_link = page["_links"]["base"] + page["_links"]["webui"]
        page_body = page["body"]["storage"]["value"]
        soup = bs4.BeautifulSoup(page_body, "html.parser")
        text = ""
        for i in soup.find_all("strong"):
            i.unwrap()
        for i in soup.select("br"):
            i.replace_with("\n")
        for i in soup.find_all():
            if i.find("ac:parameter"):
                i.decompose()
        for i in soup.find_all(["p", "li"]):
            if i.name == "li": text += '• '
            text += i.get_text() + "\n\n"
        if len(text) == 0:
            return f"Информация находится по ссылке: {page_link}"
        return text
