from flask import render_template, redirect, request, url_for
from flask_login import LoginManager, login_user, logout_user, login_required
import requests
from config import app
from cluster_analysis import ClusterAnalysis
from models import get_questions_for_clusters, Admin


login_manager = LoginManager()
login_manager.init_app(app)
analysis = ClusterAnalysis()


@login_manager.user_loader
def load_user(admin_id):
    return Admin.query.get(int(admin_id))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.check_password(password):
            login_user(admin)
            return redirect(url_for("protected"))
        else:
            return "Invalid email or password"
    else:
        return redirect(url_for("login"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/protected")
@login_required
def index() -> str:
    """Функция позволяет отрендерить главную страницу веб-сервиса.

    Returns:
        str: отрендеренная главная веб-страница.
    """
    return render_template("main-page.html", page_title="Сводка")


@app.route("/questions-analysis", methods=["POST", "GET"])
@login_required
def questions_analysis() -> str:
    """Функция позволяет вывести на экране вопросы, не имеющие ответа.

    Returns:
        str: отрендеренная веб-страница с POST-запросом на базу данных.
    """

    if request.method == "POST":
        time_start = str(request.form.get("time_start"))
        time_end = str(request.form.get("time_end"))
        have_not_answer = bool(request.form.get("have_not_answer"))
        have_low_score = bool(request.form.get("have_low_score"))
        questions = get_questions_for_clusters(
            time_start, time_end, have_not_answer, have_low_score
        )
        return render_template(
            "questions-analysis.html",
            clusters=analysis.get_clusters_keywords(questions),
            page_title="Анализ вопросов",
        )
    return render_template(
        "questions-analysis.html",
        clusters=analysis.get_clusters_keywords(get_questions_for_clusters()),
        page_title="Анализ вопросов",
    )


@app.route("/broadcast", methods=["POST", "GET"])
@login_required
def broadcast() -> str:
    """Функция позволяет отправить HTML-POST запрос на выполнение массовой рассылки на HOST чатбота.

    Returns:
        str: отрендеренная веб-страница с POST-запросом на сервер.
    """

    if request.method == "POST":
        text = request.form.get("name")
        vk_bool = bool(request.form.get("vk"))
        tg_bool = bool(request.form.get("tg"))
        response = requests.post(
            url=f"http://{app.config['CHATBOT_HOST']}/broadcast/",
            json={"text": text, "tg": tg_bool, "vk": vk_bool},
        )
        if response.status_code == 200:
            return render_template(
                "broadcast.html", page_title="Рассылка", response=response.text
            )
        else:
            response = "Ваше сообщение не доставлено"
            return render_template(
                "broadcast.html", page_title="Рассылка", response=response
            )
    return render_template("broadcast.html", page_title="Рассылка")


# @app.route("/danger-questions")
# def danger_questions() -> str:
#     """Функция позволяет вывести на экране тревожные вопросы.

#     Returns:
#         str: отрендеренная веб-страница с POST-запросом на базу данных.
#     """

#     return render_template("danger-questions.html", page_title="Тревожные вопросы")


@app.route("/settings")
@login_required
def settings() -> str:
    """Функция позволяет вывести на экране тревожные вопросы.

    Returns:
        str: отрендеренная веб-страница с POST-запросом на базу данных.
    """
    users = [
        "s.i.birvert@utmn.ru",
        "e.y.markhel@utmn.ru",
        "s.v.aleksandrova@utmn.ru",
        "v.a.vunsh@utmn.ru",
        "o.v.loginova@utmn.ru",
        "e.a.mukhina@utmn.ru",
        "o.v.fedorina@utmn.ru",
    ]

    return render_template("settings.html", users=users, page_title="Настройки")


@app.route("/reindex", methods=["POST"])
@login_required
def reindex_qa():
    """Функция отправляет POST-запрос на переиндексацию в модуле QA.

    Returns:
        str: Статус отправки запроса.
    """
    requests.post(f"http://{app.config['QA_HOST']}/reindex/")
    return redirect(url_for("settings"))
