import logging
from langchain.prompts import PromptTemplate
from langchain_community.llms import GigaChat
from config import Config

llm = GigaChat(
    model=Config.GIGACHAT_MODEL,
    credentials=Config.GIGACHAT_TOKEN,
    verify_ssl_certs=False,
)
prompt_template = """Действуйте как Вопрошалыч — инновационный виртуальный помощник студента ТюмГУ.
Используйте следующий документ в тройных кавычках, чтобы кратко ответить на вопрос студента.
Оставьте ссылки, адреса и телефоны как есть. Если ответа в тексте нет, напишите "ответ не найден", не пытайтесь ничего придумать.
Предоставьте краткий, точный и полезный ответ, чтобы помочь студентам чувствовать себя в университете комфортно и безопасно :)

Документ, найденный умной системой:
\"\"\"
{context}
\"\"\"

Вопрос студента: {question}"""
prompt = PromptTemplate.from_template(prompt_template)
chain = prompt | llm


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
        return chain.invoke(query).replace('"""', "").strip()
    except Exception as e:
        logging.error(e)
        return ""
