# Микросервис QA

## Описание
Микросервис, предоставляющий API для:
 * генерации ответа на вопрос, опираясь на документы из вики-системы;
 * обновления векторного индекса текстов документов из вики-системы.

 > [!IMPORTANT]
> Информация о настройке взаимодействия с вики-системой Confluence представлена в [confluence-integration.md](confluence-integration.md).

## [main](../qa/main.py)

### `qa(request: web.Request) -> web.Response`
Возвращает ответ на вопрос пользователя и ссылку на источник

    Args:
        request (web.Request): запрос, содержащий `question`

    Returns:
        web.Response: ответ

### `reindex(request: web.Request) -> web.Response`
Пересоздаёт векторный индекс текстов для ответов на вопросы

    Args:
        request (web.Request): запрос

    Returns:
        web.Response: ответ

## [config](../qa/config.py)

### `class Config`
Класс с переменными окружения

## [database](../qa/database.py)

### `class Chunk(Base)`
Фрагмент документа из вики-системы

    Args:
        confluence_url (str): ссылка на источник
        text (str): текст фрагмента
        embedding (Vector): векторное представление текста фрагмента размерностью 1024

## [confluence_retrieving](../qa/confluence_retrieving.py)

### `get_document_content_by_id(confluence: Confluence, page_id: str) -> tuple[str | None, str | None]`
Возвращает содержимое страницы на Confluence после предобработки с помощью PyPDF или BS4 и ссылку на страницу

    Args:
        confluence (Confluence): экземпляр Confluence
        page_id (str): ID страницы

    Returns:
        tuple[str | None, str | None]: содержимое страницы, ссылка на страницу

### `reindex_confluence(engine: Engine, text_splitter: TextSplitter, encoder_model: SentenceTransformer)`
Пересоздаёт векторный индекс текстов для ответов на вопросы. При этом обрабатываются страницы, не имеющие вложенных страниц.

    Args:
        engine (Engine): экземпляр подключения к БД
        text_splitter (TextSplitter): разделитель текста на фрагменты
        encoder_model (SentenceTransformer): модель получения векторных представлений Sentence Transformer

### `get_chunk(engine: Engine, encoder_model: SentenceTransformer, question: str) -> Chunk | None`
Возвращает ближайший к вопросу фрагмент документа Chunk из векторной базы данных

    Args:
        engine (Engine): экземпляр подключения к БД
        encoder_model (SentenceTransformer): модель получения векторных представлений SentenceTransformer
        question (str): вопрос пользователя

    Returns:
        Chunk | None: экземпляр класса Chunk — фрагмент документа

## [llm_prompting](../qa/llm_prompting.py)

### `get_answer(context: str, question: str) -> str`
Возвращает сгенерированный LLM ответ на вопрос пользователя по заданному документу в соответствии с промтом

    Args:
        context (str): текст документа (или фрагмента документа)
        question (str): вопрос пользователя

    Returns:
        str: экземпляр класса Chunk — фрагмент документа

## [tests](../qa/tests.py)

### `test_llm()`
тест взаимодействия с LLM

### `test_confluence()`
тест взаимодействия с Confluence
