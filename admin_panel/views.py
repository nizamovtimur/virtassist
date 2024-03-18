from config import app
from models import db, User, Chunk, QuestionAnswer

from flask import render_template, request
import requests


@app.route('/')
def index() -> str:
    """Функция позволяет отрендерить главную страницу веб-сервиса.

    Arguments: 
        None

    Returns:
        str: отрендеренная главная веб-страница.
    """
    return render_template('main-page.html')


@app.route('/broadcast', methods=['POST', 'GET'])
def broadcast() -> str:
    """Функция позволяет отправить HTML-POST запрос на выполнение массовой рассылки на HOST чатбота.

    Arguments: 
        None

    Returns:
        str: отрендеренная веб-страница с POST-запросом на сервер.
    """
    if request.method == 'POST':
        text = request.form.get('name')
        vk_bool = request.form.get('vk')
        tg_bool = request.form.get('telegram')
        try:
            response = requests.post(url=f"http://{app.config['CHATBOT_HOST']}/broadcast",
                                     json={"text": text, "to_tg": tg_bool, "to_vk": vk_bool})
            return render_template('broadcast.html', response=response.text)
        except:
            response = 'Ваше сообщение не доставлено'
            return render_template('broadcast.html', response=response)
    else:
        return render_template('broadcast.html')


@app.route('/questions-wo-ans')
def questions() -> str:
    """Функция позволяет вывести на экране вопросы, не имеющие ответа.

    Arguments: 
        None

    Returns:
        str: отрендеренная веб-страница с POST-запросом на базу данных.
    """
    return render_template('questions-wo-ans.html')


@app.route('/danger-q')
def dangers() -> str:
    """Функция позволяет вывести на экране тревожные вопросы.

    Arguments: 
        None

    Returns:
        str: отрендеренная веб-страница с POST-запросом на базу данных.
    """
    return render_template('danger-q.html')
