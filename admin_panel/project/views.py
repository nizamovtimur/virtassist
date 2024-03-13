from config import app
from models import db, User, Chunk, QuestionAnswer

from flask import render_template, request, redirect
import requests


@app.route('/')
def index():
    return render_template('main-page.html')


@app.route('/broadcast', methods=['POST', 'GET'])
def broadcast():
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
def questions():
    return render_template('questions-wo-ans.html')


@app.route('/danger-q')
def dangers():
    return render_template('danger-q.html')
