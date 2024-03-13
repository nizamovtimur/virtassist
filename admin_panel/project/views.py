from config import app
from models import db, User, Chunk, QuestionAnswer

from flask import render_template


@app.route('/')
def index():
    return render_template('main-page.html')


@app.route('/broadcast')
def broadcast():
    return render_template('broadcast.html')
