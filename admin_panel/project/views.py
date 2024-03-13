from config import app
from models import db, User, Chunk, QuestionAnswer

from flask import render_template, request
import requests


@app.route('/')
def index():
    return render_template('main-page.html')


@app.route('/broadcast', methods=['POST'])
def broadcast():
    requests.post()
    return render_template('broadcast.html')
