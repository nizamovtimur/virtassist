import os

os.environ["ABBREVIATION_UTMN"] = (
    "тюмгу шкн игип фэи соцгум ипип биофак инзем инхим фти инбио ифк ед шпи шен уиот"
)

os.environ["ENVIRONMENT"] = "test"

from config import app
from flask_sqlalchemy import SQLAlchemy
from cluster_analysis import ClusterAnalysis, mark_of_question
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from models import *
from datetime import datetime, timedelta


class TestClusterAnalysis:
    """Класс с функцией тестирования анализа вопросов"""

    def test_preprocessing(self):
        """Функция тестирует анализ вопросов"""

        # Импорт тестовых данных
        arr = []
        with open("test_db.csv", "r", encoding="utf-8") as f:
            s = f.readline()
            while s:
                x = int(s.split(" --- ")[2])
                if x == 0:
                    x = mark_of_question.have_not_answer
                elif x == 1:
                    x = mark_of_question.have_low_score
                elif x == 2:
                    x = mark_of_question.have_high_score
                else:
                    x = mark_of_question.have_not_score
                arr.append(
                    {
                        "text": s.split(" --- ")[0],
                        "date": s.split(" --- ")[1],
                        "type": x,
                    }
                )
                s = f.readline()
        # Обработка
        CA = ClusterAnalysis()
        data = CA.get_clusters_keywords(arr)
        # Сравнение с эталоном
        with open("test_true_result.csv", "r", encoding="utf-8") as f:
            assert data[2] == int(f.readline()[:-1])  # Количество кластеров
            assert data[1] == int(f.readline()[:-1])  # Количество вопросов
            assert "" == f.readline()[:-1]
            for ar in data[0]:  # Проверяем каждый кластер
                assert len(ar[0]) == int(f.readline()[:-1])  # Объём кластера
                for a in ar[1]:
                    assert (
                        a == f.readline()[:-1]
                    )  # Все ключевые слова и выражения по кластеру
                assert (
                    ar[2][0] == f.readline()[:-1]
                )  # Дата получения чат-ботом первого вопроса в кластере
                assert (
                    ar[2][1] == f.readline()[:-1]
                )  # Дата получения чат-ботом последнего вопроса в кластере
                assert "" == f.readline()[:-1]


class TestModels:
    """Класс с функциями тестирования моделей административной панели"""

    with app.app_context():
        db.create_all()

    def test_get_admins(self):
        """Функция тестирует получение списка администраторов"""

        with app.app_context():
            with Session(db.engine) as session:
                admin_1 = Admin(
                    name="name_1",
                    surname="surname_1",
                    email="123@mail.com",
                    department="cit",
                )

                password = "123456"
                admin_1.set_password(password=password)

                admin_2 = Admin(
                    name="name_2",
                    surname="surname_2",
                    last_name="last_name_2",
                    email="456@mail.com",
                    department="iot",
                )

                password = "789100"
                admin_2.set_password(password=password)

                session.add(admin_1)
                session.add(admin_2)
                session.commit()

        with app.app_context():
            admins = get_admins()
            assert admins[0].name == "name_1"
            assert admins[0].surname == "surname_1"
            assert admins[0].last_name is None
            assert admins[0].email == "123@mail.com"
            assert admins[0].department == "cit"

            assert admins[1].name == "name_2"
            assert admins[1].surname == "surname_2"
            assert admins[1].last_name is not None
            assert admins[1].last_name == "last_name_2"
            assert admins[1].email == "456@mail.com"
            assert admins[1].department == "iot"

    def test_get_questions_for_clusters(self):
        """Функция тестирует получение вопросов из кластеров"""

        def sort_by_question_number(item):
            return int(item["text"].replace("Вопрос", ""))

        time_start = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        time_end = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        with app.app_context():
            with Session(db.engine) as session:
                questions = [
                    QuestionAnswer(
                        question="Вопрос1",
                        answer="Ответ1",
                        score=None,
                        user_id=2,
                        created_at=datetime.now(),
                    ),
                    QuestionAnswer(
                        question="Вопрос2",
                        answer="Ответ2",
                        score=1,
                        user_id=2,
                        created_at=datetime.now() - timedelta(days=1),
                    ),
                    QuestionAnswer(
                        question="Вопрос3",
                        answer="",
                        score=None,
                        user_id=3,
                        created_at=datetime.now() - timedelta(days=2),
                    ),
                    QuestionAnswer(
                        question="Вопрос4",
                        answer="Ответ4",
                        score=1,
                        user_id=3,
                        created_at=datetime.now() - timedelta(days=1),
                    ),
                    QuestionAnswer(
                        question="Вопрос5",
                        answer="Ответ5",
                        score=5,
                        user_id=4,
                        created_at=datetime.now() - timedelta(days=2),
                    ),
                    QuestionAnswer(
                        question="Вопрос6",
                        answer="",
                        score=None,
                        user_id=5,
                        created_at=datetime.now() - timedelta(days=1),
                    ),
                ]
                session.add_all(questions)
                session.commit()
            result = get_questions_for_clusters(
                time_start, time_end, True, False, False, False
            )
            assert len(result) == 2
            assert result[0]["text"] == "Вопрос3"
            assert result[1]["text"] == "Вопрос6"
            assert result[0]["type"] == mark_of_question.have_not_answer
            result = get_questions_for_clusters(
                time_start, time_end, False, True, False, False
            )
            assert len(result) == 2
            assert result[0]["text"] == "Вопрос2"
            assert result[1]["text"] == "Вопрос4"
            assert result[0]["type"] == mark_of_question.have_low_score
            result = get_questions_for_clusters(
                time_start, time_end, False, False, True, False
            )
            assert len(result) == 1
            assert result[2]["text"] == "Вопрос5"
            assert result[0]["type"] == mark_of_question.have_high_score
            result = get_questions_for_clusters(
                time_start, time_end, False, False, False, True
            )
            assert len(result) == 2
            assert result[0]["text"] == "Вопрос1"
            assert result[1]["text"] == "Вопрос6"
            assert result[0]["type"] == mark_of_question.have_not_score
            result = get_questions_for_clusters(
                time_start, time_end, True, True, False, False
            )
            assert len(result) == 4
            assert result[0]["text"] == "Вопрос3"
            assert result[1]["text"] == "Вопрос6"
            assert result[2]["text"] == "Вопрос2"
            assert result[3]["text"] == "Вопрос4"
            assert result[0]["type"] == mark_of_question.have_not_answer
            assert result[2]["type"] == mark_of_question.have_low_score
            result = get_questions_for_clusters(
                time_start, time_end, True, True, True, False
            )
            assert len(result) == 5
            assert result[0]["text"] == "Вопрос3"
            assert result[1]["text"] == "Вопрос6"
            assert result[2]["text"] == "Вопрос2"
            assert result[3]["text"] == "Вопрос4"
            assert result[6]["text"] == "Вопрос5"
            assert result[0]["type"] == mark_of_question.have_not_answer
            assert result[2]["type"] == mark_of_question.have_low_score
            assert result[4]["type"] == mark_of_question.have_high_score
            assert result[6]["type"] == mark_of_question.have_high_score
            result = get_questions_for_clusters(
                time_start, time_end, True, True, True, True
            )
            assert len(result) == 6
            assert result[0]["text"] == "Вопрос3"
            assert result[1]["text"] == "Вопрос6"
            assert result[2]["text"] == "Вопрос2"
            assert result[3]["text"] == "Вопрос4"
            assert result[4]["text"] == "Вопрос5"
            assert result[6]["text"] == "Вопрос5"
            assert result[5]["text"] == "Вопрос1"
            assert result[0]["type"] == mark_of_question.have_not_answer
            assert result[1]["type"] == mark_of_question.have_not_answer
            assert result[2]["type"] == mark_of_question.have_low_score
            assert result[3]["type"] == mark_of_question.have_low_score
            assert result[4]["type"] == mark_of_question.have_high_score
            assert result[5]["type"] == mark_of_question.have_not_score
