from atlassian import Confluence
from config import Config
from gigachat_prompting import get_answer
from confluence_retrieving import get_document_content_by_id


def test_gigachat():
    """тест взаимодействия с GigaChat"""

    context = """Чтобы поменять занятия по физической культуре на посещение
    частного фитнес-клуба, необходимо заполнить заявление и обратиться
    к курирующему преподавателю"""
    question = "Что нужно сделать, чтобы заменить физру на частный клуб?"
    assert "препод" in get_answer(context, question).lower()
    assert "не найден" in get_answer(context, "Когда наступит лето?").lower()


def test_confluence():
    """тест взаимодействия с Confluence"""

    confluence = Confluence(url=Config.CONFLUENCE_HOST, token=Config.CONFLUENCE_TOKEN)
    main_space = confluence.get_space(
        Config.CONFLUENCE_SPACES[0], expand="description.plain,homepage"
    )
    page_content, page_link = get_document_content_by_id(
        confluence, str(main_space["homepage"]["id"])
    )
    assert page_content is not None
    assert len(page_content) > 10
    assert (
        page_link
        == main_space["_links"]["base"] + main_space["homepage"]["_links"]["webui"]
    )
