from core import app
from core.models import db, User, Chunk, QuestionAnswer


@app.route('/')
def index():
    return "<h1>Hello World</h1>"
