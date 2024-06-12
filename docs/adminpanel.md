# Микросервис Adminpanel

## Описание
Административная панель виртуального помощника студента для анализа вопросов и организации массовых рассылок.

> [!IMPORTANT]
> Информация о настройке взаимодействия с вики-системой Confluence представлена в [confluence-integration.md](confluence-integration.md).

## [cluster_analysis](../adminpanel/cluster_analysis.py)

### `class ClusterAnalysis`
Модуль кластерного анализа

#### `preprocessing(df: pd.DataFrame) -> pd.DataFrame`
Метод предобработки данных

    Args:
        df (pd.DataFrame): датафрейм содержания и даты появления вопроса

    Returns:
        pd.DataFrame: отредактированный датафрейм без спецсимволов и мусорных вопросов

##### `del_spec_sim(s: str) -> str`
Метод удаляет специальные символы и двойные пробелы

    Args:
        s (str): предложение, которое нужно предобработать

    Returns:
        str: предложение без спецсимволов и двойных пробелов

##### `found_trash_words(words: str) -> str`
Метод помечает на удаление предложений, которые по большей части состоят из бессмысленных наборов букв

    Args:
        words (str): предложение, которое нужно предобработать

    Returns:
        str | None: предложение, если состоит по большей части из осмысленных слов, иначе None

#### `vectorization(df: pd.DataFrame) -> np.ndarray`
Метод векторизации предложений, подлежащих анализу

    Args:
        df (pd.DataFrame): датафрейм содержания и даты появления вопроса

    Returns:
        np.ndarray: массив, содержащий в каждой строке векторные представления вопросов

#### `clustering(vectors: np.ndarray, df: pd.DataFrame) -> dict[int, list[tuple[str, str]]]`
Метод кластеризации предложений

    Args:
        vectors (np.ndarray): массив, содержащий в каждой строке векторные представления вопросов
        df (pd.DataFrame): датафрейм содержания и даты появления вопроса
    Returns:
        dict[int, list[tuple[str, str]]]: словарь, содержащий предложения с датами по кластерам

#### `keywords_extracting(sentences: list[str]) -> list[str]`
Метод формирующий ключевые слова и выражения по списку предложений

    Args:
        sentences (list[str]): список предложений, по которым нужно составить ключевые слова

    Returns:
        list[str]: ключевые слова и выражения

#### `get_clusters_keywords(questions: list[dict[str, str]]) -> list[tuple[list[tuple[str, mark_of_question]], list[str], tuple[str, str]]], int, int]`
Логика кластеризации текстовых данных

    Args:
        questions (list[dict[str, str]]): список вопросов, подлежащих анализу

    Returns:
        tuple[list[tuple[list[tuple[str, mark_of_question]], list[str], tuple[str, str]]], int, int]: кортеж, где 0 - список кортежей, для каждого: список вопросов с метками, список ключевых слов, временной промежуток вопросов по кластеру, 1 - количество вопросов, 2 - количество кластеров

## [config](../adminpanel/config.py)
Файл конфигурации административной панели виртуального помощника

## [models](../adminpanel/models.py)

### `class Chunk(db.Model)`
Фрагмент документа из вики-системы

    Args:
        confluence_url (str): ссылка на источник
        text (str): текст фрагмента
        embedding (Vector): векторное представление текста фрагмента размерностью 1024
        created_at (datetime): время создания модели
        updated_at (datetime): время обновления модели

### `class User(db.Model)`
Пользователь чат-бота

    Args:
        id (int): id пользователя
        vk_id (int | None): id пользователя ВКонтакте
        telegram_id (int | None): id пользователя Telegram
        is_subscribed (bool): состояние подписки пользователя
        question_answers (List[QuestionAnswer]): вопросы пользователя
        created_at (datetime): время создания модели
        updated_at (datetime): время обновления модели

### `class QuestionAnswer(db.Model)`
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

### `class Admin(db.Model, UserMixin)`
Администратор панели

    Args:
        id (int): id администратора
        name (str): имя
        surname (str): фамилия
        last_name (str | None): отчество (опционально)
        email (str): корпоративная электронная почта
        department (str): подразделение
        created_at (datetime): время создания модели
        updated_at (datetime): время обновления модели

#### `set_password(password: str) -> None`
Метод хеширования пароля администратора

    Args:
        password (str): пароль администратора

#### `check_password(password: str) -> bool`
Метод проверки введенного администратором пароля

    Args:
        password (str): пароль администратора

    Returns:
        bool: проверка, совпадает ли введенный пароль с хешированным паролем

### `get_questions_for_clusters(time_start: str, time_end: str, have_not_answer: bool, have_low_score: bool, have_high_score: bool, have_high_score: bool`
Функция для выгрузки вопросов в классе `ClusterAnalysis`

    Args:
        time_start (str): дата, от которой нужно сортировать вопросы. По-умолчанию, 30 дней назад
        time_end (str): дата, до которой нужно сортировать вопросы. По-умолчанию, завтрашняя дата
        have_not_answer (bool): вопросы без ответа
        have_low_score (bool): вопросы с низкой оценкой
        have_high_score (bool): вопросы с высокой оценкой
        have_not_score (bool): вопросы без оценки

    Returns:
        list[dict[str, str | mark_of_question]]: список вопросов - словарей с ключами `text`, `date` и `type`

### `get_questions_count(time_start: str, time_end: str) -> dict[str, list[int]]`
Функция подсчёта вопросов, заданных в вк и телеграм, по дням для графиков на `main-page.html`

    Args:
        time_start (str): дата начала периода
        time_end (str): дата конца периода

    Returns:
        dict[str, list[int]]: словарь из дат с количеством вопросов по дням в vk и telegram

### `get_admins() -> list[Admin]`
Функция для выгрузки администраторов из БД

    Returns:
        list[Admin]: список администраторов

## [save_nltk](../adminpanel/save_nltk.py)
Файл, который сохраняет NLTK для кластерного анализа при сборке приложения

## [tests](../adminpanel/tests.py)

### `class TestClusterAnalysis`
Класс с функцией тестирования анализа вопросов

#### `test_preprocessing()`
Функция тестирует анализ вопросов

### `class TestModels`
Класс с функциями тестирования моделей административной панели

#### `test_get_admins()`
Функция тестирует получение списка администраторов

#### `test_get_questions_for_clusters()`
Функция тестирует получение вопросов из кластеров

## [views](../adminpanel/views.py)

### `load_user(id)`
Функция загружает в `login_manager` уникальный идентификатор администратора

    Args:
        id: уникальный идентификатор администратора

    Returns:
        Admin.query.get(int(id)): объект - администратор

### `login() -> str`
Функция авторизует пользователя, если данные для входа совпадают

    Returns:
        str: отрендеренная главная веб-страница сервиса

### `logout() -> str`
Функция деавторизует пользователя

    Returns:
        str: отрендеренная веб-страница авторизации

### `index() -> str`
Функция рендерит главную страницу веб-сервиса

    Returns:
        str: отрендеренная главная веб-страница

### `questions_analysis() -> str`
Функция выводит на экране вопросы, не имеющие ответа

    Returns:
        str: отрендеренная веб-страница с POST-запросом на базу данных

### `broadcast() -> str`
Функция отправляет HTML-POST запрос на выполнение массовой рассылки на HOST чатбота

    Returns:
        str: отрендеренная веб-страница с POST-запросом на сервер

### `settings() -> str`
Функция выводит интерфейс взаимодействия с администраторами панели и с непосредственно модулем QA

    Returns:
        str: отрендеренная веб-страница настроек администраторов и возможностью провести переиндексацию

### `reindex_qa() -> str`
Функция отправляет POST-запрос на переиндексацию в модуле QA

    Returns:
        str: статус отправки запроса

## [wsgi](../adminpanel/wsgi.py)
Файл инициирует работу веб-приложения на сервере
