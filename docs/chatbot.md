# Микросервис Chatbot

## Описание
Микросервис, обрабатывающий LongPoll API-запросы чат-ботов VK и Telegram.

> [!IMPORTANT]
> Информация о настройке взаимодействия с вики-системой Confluence представлена в [confluence-integration.md](confluence-integration.md).

## [main](../chatbot/main.py)

### `vk_keyboard_choice(notify_text: str) -> str`
Возвращает клавиатуру из кнопок предоставления справочной информации и подписки на рассылку (если пользователь подписан, то отписки от неё) для чат-бота ВКонтакте

    Args:
        notify_text (str): "Подписаться на рассылку" если пользователь не подписан, иначе "Отписаться от рассылки"

    Returns:
        str: JSON-объект, описывающий клавиатуру с шаблонами сообщений

### `tg_keyboard_choice(notify_text: str) -> tg.types.ReplyKeyboardMarkup`
Возвращает клавиатуру из кнопок предоставления справочной информации и подписки на рассылку (если пользователь подписан, то отписки от неё) для чат-бота Telegram

    Args:
        notify_text (str): "Подписаться на рассылку" если пользователь не подписан, иначе "Отписаться от рассылки"

    Returns:
        tg.types.ReplyKeyboardMarkup: клавиатура с шаблонами сообщений

### `vk_send_confluence_keyboard(message: VKMessage, question_types: list)`
Создаёт inline-кнопки для чат-бота ВКонтакте на основе справочной структуры пространства в вики-системе

    Args:
        message (VKMessage): сообщение пользователя
        question_types (list): страницы или подстраницы из структуры пространства в вики-системе

### `tg_send_confluence_keyboard(message: tg.types.Message, question_types: list)`
Создаёт inline-кнопки для чат-бота Telegram на основе справочной структуры пространства в вики-системе

    Args:
        message (tg.types.Message): сообщение пользователя
        question_types (list): страницы или подстраницы из структуры пространства в вики-системе

### `vk_handler(message: VKMessage)`
Обработчик события (для чат-бота ВКонтакте), при котором пользователь запрашивает справочную информацию

    Args:
        message (VKMessage): сообщение, отправленное пользователем при запросе справочной информации

### `tg_handler(message: tg.types.Message)`
Обработчик события (для чат-бота Telegram), при котором пользователь запрашивает справочную информацию

    Args:
        message (tg.types.Message): сообщение, отправленное пользователем при запросе справочной информации

### `vk_confluence_parse(message: VKMessage)`
Обработчик события (для чат-бота ВКонтакте), при котором пользователь нажимает на кнопку, относящуюся к типу или подтипу вопросов

    Args:
        message (VKMessage): сообщение пользователя

### `tg_confluence_parse(callback: tg.types.CallbackQuery)`
Обработчик события (для чат-бота Telegram), при котором пользователь нажимает на кнопку, относящуюся к типу или подтипу вопросов

    Args:
        callback (tg.types.CallbackQuery): запрос при нажатии на inline-кнопку

### `vk_rate(message: VKMessage)`
Обработчик события (для чат-бота ВКонтакте), при котором пользователь оценивает ответ на вопрос

    Args:
        message (VKMessage): сообщение пользователя

### `tg_rate(callback_query: tg.types.CallbackQuery)`
Обработчик события (для чат-бота Telegram), при котором пользователь оценивает ответ на вопрос

    Args:
        callback_query (tg.types.CallbackQuery): запрос при нажатии на inline-кнопку

### `vk_subscribe(message: VKMessage)`
Обработчик события (для чат-бота ВКонтакте), при котором пользователь оформляет или снимает подписку на рассылку

    Args:
        message (VKMessage): сообщение пользователя

### `tg_subscribe(message: tg.types.Message)`
Обработчик события (для чат-бота Telegram), при котором пользователь оформляет или снимает подписку на рассылку

    Args:
        message (tg.types.Message): сообщение пользователя

### `get_answer(question: str) -> tuple[str, str | None]`
Получение ответа на вопрос с использованием микросервиса

    Args:
        question (str): вопрос пользователя

    Returns:
        tuple[str, str | None]: ответ на вопрос и ссылка на страницу в вики-системе

### `vk_answer(message: VKMessage)`
Обработчик события (для чат-бота ВКонтакте), при котором пользователь задаёт вопрос чат-боту

После отображения ответа на вопрос чат-бот отправляет inline-кнопки для оценивания ответа

    Args:
        message (VKMessage): сообщение пользователя с вопросом

### `tg_start(message: tg.types.Message)`
Обработчик события (для чат-бота Telegram), при котором пользователь отправляет команду /start

    Args:
        message (tg.types.Message): сообщение пользователя

### `tg_answer(message: tg.types.Message)`
Обработчик события (для чат-бота Telegram), при котором пользователь задаёт вопрос чат-боту

После отображения ответа на вопрос чат-бот отправляет inline-кнопки для оценивания ответа

    Args:
        message (tg.types.Message): сообщение с вопросом пользователя

### `broadcast(request: web.Request) -> web.Response`
Создает рассылку в ВК и/или ТГ

    Args:
        request (web.Request): запрос, содержащий `text`, булевые `tg`, `vk`

    Returns:
        web.Response: ответ

### `launch_vk_bot()`
Функция начала работы чат-бота ВКонтакте

### `launch_telegram_bot()`
Функция начала работы чат-бота Telegram

### `run_web_app()`
Функция запуска сервера для принятия запроса на рассылку

## [confluence_interaction](../chatbot/confluence_interaction.py)
### `make_markup_by_confluence() -> list`
Возвращает справочную структуру пространства в вики-системе

Проводится часовое кэширование

    Returns:
        list: список основных страниц из структуры пространства в вики-системе

### `parse_confluence_by_page_id(id: int | str) -> list | str`
Возвращает текст страницы из структуры пространства в вики-системы или список вложенных страниц по id

Проводится часовое кэширование

    Args:
        id (int | str): id страницы

    Returns:
        list | str: список вложенных страниц или текст страницы

## [strings](../chatbot/strings.py)
### `class Strings`
Класс со строковыми представлениями отправляемых чат-ботом сообщений

## [config](../chatbot/config.py)
### `class Config`
Класс с переменными окружения

## [database](../chatbot/database.py)
### `class User(Base)`
Пользователь чат-бота

    Args:
        id (int): id пользователя
        vk_id (int | None): id пользователя ВКонтакте
        telegram_id (int | None): id пользователя Telegram
        is_subscribed (bool): состояние подписки пользователя
        question_answers (List[QuestionAnswer]): вопросы пользователя
        created_at (datetime): время создания модели
        updated_at (datetime): время обновления модели

### `class QuestionAnswer(Base)`
Вопрос пользователя с ответом на него

    Args:
        id (int): id ответа
        question (str): вопрос пользователя
        answer (str | None): ответ на вопрос пользователя
        confluence_url (str | None): ссылка на страницу в вики-системе, содержащую ответ
        score (int | None): оценка пользователем ответа
        user_id (int): id пользователя, задавшего вопрос
        user (User): пользователь, задавший вопрос
        created_at (datetime): время создания модели
        updated_at (datetime): время обновления модели

### `add_user(engine: Engine, vk_id: int | None = None, telegram_id: int | None = None) -> tuple[bool, int]`
Функция добавления в БД пользователя виртуального помощника

    Args:
        engine (Engine): подключение к БД
        vk_id (int | None): id пользователя ВКонтакте
        telegram_id (int | None): id пользователя Telegram

    Raises:
        TypeError: vk_id и telegram_id не могут быть None в одно время

    Returns:
        tuple[bool, int]: добавился пользователь или нет, какой у него id в БД

### `get_user_id(engine: Engine, vk_id: int | None = None, telegram_id: int | None = None) -> int | None`
Функция получения из БД пользователя

    Args:
        engine (Engine): подключение к БД
        vk_id (int | None): id пользователя ВКонтакте
        telegram_id (int | None): id пользователя Telegram

    Raises:
        TypeError: vk_id и telegram_id не могут быть None в одно время

    Returns:
        int | None: id пользователя или None

### `subscribe_user(engine: Engine, user_id: int) -> bool`
Функция оформления подписки пользователя на рассылку

    Args:
        engine (Engine): подключение к БД
        user_id (int): id пользователя

    Returns:
        bool: подписан пользователь или нет

### `check_subscribing(engine: Engine, user_id: int) -> bool`
Функция проверки подписки пользователя на рассылку

    Args:
        engine (Engine): подключение к БД
        user_id (int): id пользователя

    Returns:
        bool: подписан пользователь или нет

### `check_spam(engine: Engine, user_id: int) -> bool`
Функция проверки на спам

    Args:
        engine (Engine): подключение к БД
        user_id (int): id пользователя

    Returns:
        bool: пользователь задал три вопроса за последнюю минуту

### `add_question_answer(engine: Engine, question: str, answer: str, confluence_url: str | None, user_id: int) -> int`
Функция добавления в БД вопроса пользователя с ответом на него

    Args:
        engine (Engine): подключение к БД
        question (str): вопрос пользователя
        answer (str): ответ на вопрос пользователя
        confluence_url (str | None): ссылка на страницу в вики-системе, содержащую ответ
        user_id (int): id пользователя

    Returns:
        int: id вопроса с ответом на него

### `rate_answer(engine: Engine, question_answer_id: int, score: int) -> bool`
Функция оценивания ответа на вопрос

    Args:
        engine (Engine): подключение к БД
        question_answer_id (int): id вопроса с ответом
        score (int): оценка ответа

    Returns:
        bool: удалось добавить в БД оценку ответа или нет

### `get_subscribed_users(engine: Engine) -> tuple[list[int | None], list[int | None]]`
Функция для получения подписанных на рассылки пользователей

    Args:
        engine (Engine): подключение к БД

    Returns:
        tuple[list[int], list[int]]: кортеж списков с id пользователей VK и Telegram

## [tests](../chatbot/tests.py)
### `class TestDBFunctions`
Класс с функциями тестирования функций, взаимодействующих с БД

### `test_add_get_user(self)`
Тест добавления и получения пользователя по id

### `test_subscribing(self)`
Тест оформления подписки пользователя на рассылку

### `test_get_subscribed_users(self)`
Тест получения списков подписанных пользователей

### `test_rate_answer(self)`
Тест функции оценивания ответа

### `test_check_spam(self)`
Тест функции, проверяющей спам
