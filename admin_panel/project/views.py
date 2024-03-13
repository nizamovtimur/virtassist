from config import app
from models import db, User, Chunk, QuestionAnswer

from flask import render_template, request
import requests


@app.route('/')
def index():
    return render_template('main-page.html')


@app.route('/broadcast', methods=['POST', 'GET'])
def broadcast():
    if request.method == 'POST':
        text = request.form.get('name')
        requests.post(url=f"http://{app.config['CHATBOT_HOST']}/broadcast",
                      json={"text": text})
        return 'Hello world'
    else:
        return render_template('broadcast.html')
