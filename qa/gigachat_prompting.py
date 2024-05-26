import logging
from langchain.prompts import PromptTemplate
from langchain_community.llms import GigaChat
from config import Config

giga = GigaChat(credentials=Config.GIGACHAT_TOKEN, verify_ssl_certs=False)
prompt_template = """Действуй как Вопрошалыч — виртуальный помощник студента ТюмГУ.
Используй следующий текст в тройных кавычках, чтобы кратко ответить на вопрос студента.
Не придумывай и не изменяй ссылки, адреса и телефоны. Если ответа в тексте нет, напиши "ответ не найден".

\"\"\"
{context}
\"\"\"

Вопрос студента: {question}"""
prompt = PromptTemplate.from_template(prompt_template)
giga_chain = prompt | giga


def get_answer(context: str, question: str) -> str:
    """Возвращает сгенерированный LLM ответ на вопрос пользователя
    по заданному документу в соответствии с промтом

    Args:
        context (str): текст документа (или фрагмента документа)
        question (str): вопрос пользователя

    Returns:
        str: экземпляр класса Chunk — фрагмент документа
    """

    query = {"context": context, "question": question}
    try:
        return giga_chain.invoke(query).replace('"""', "").strip()
    except Exception as e:
        logging.error(e)
        return ""
