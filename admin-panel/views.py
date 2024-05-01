import requests
from flask import render_template, request
from config import app
from models import get_questions_for_clusters
from cluster_analisys import ClusterAnalisys

analisys = ClusterAnalisys()
@app.route('/')
def index() -> str:
    """Функция позволяет отрендерить главную страницу веб-сервиса.

    Returns:
        str: отрендеренная главная веб-страница.
    """
    return render_template('main-page.html')


@app.route('/reindex', methods=['POST'])
def reindex_qa():
    """Функция отправляет POST-запрос на переиндексацию в модуле QA.

    Returns:
        str: Статус отправки запроса.
    """
    requests.post(f"http://{app.config['QA_HOST']}/reindex/")
    return render_template('main-page.html')


@app.route('/broadcast', methods=['POST', 'GET'])
def broadcast() -> str:
    """Функция позволяет отправить HTML-POST запрос на выполнение массовой рассылки на HOST чатбота.

    Returns:
        str: отрендеренная веб-страница с POST-запросом на сервер.
    """

    if request.method == 'POST':
        text = request.form.get('name')
        vk_bool = request.form.get('vk')
        tg_bool = request.form.get('telegram')
        response = requests.post(url=f"http://{app.config['CHATBOT_HOST']}/broadcast/",
                                 json={"text": text, "tg": tg_bool, "vk": vk_bool})
        if response.status_code == 200:
            return render_template('broadcast.html', response=response.text)
        else:
            response = 'Ваше сообщение не доставлено'
            return render_template('broadcast.html', response=response)
    else:
        return render_template('broadcast.html')


@app.route('/questions-wo-answers')
def questions(methods=['POST', 'GET']) -> str:
    """Функция позволяет вывести на экране вопросы, не имеющие ответа.

    Returns:
        str: отрендеренная веб-страница с POST-запросом на базу данных.
    """
    if request.method == 'POST':
        time_start = request.form.get('time_start')
        time_end = request.form.get('time_end')
        have_answer = request.form.get('have_answer')
        have_score = request.form.get('have_score')
        clusters = analisys.get_clusters_keywords(get_questions_for_clusters(time_start, time_end, have_answer, have_score))
        return render_template('questions-wo-answers.html', clusters=clusters, page_title='Вопросы без ответов')
    else:
        return render_template('questions-wo-answers.html', clusters=[], page_title='Вопросы без ответов')

@app.route('/danger-questions')
def dangers() -> str:
    """Функция позволяет вывести на экране тревожные вопросы.

    Returns:
        str: отрендеренная веб-страница с POST-запросом на базу данных.
    """

    return render_template('danger-questions.html')
