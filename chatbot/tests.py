import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from database import (
    Base,
    QuestionAnswer,
    add_user,
    get_subscribed_users,
    get_user_id,
    subscribe_user,
    check_subscribing,
    check_spam,
    add_question_answer,
    rate_answer,
)


class TestDBFunctions:
    """Класс с функциями тестирования функций, взаимодействующих с БД"""

    engine = create_engine("sqlite://", echo=True)
    Base.metadata.create_all(engine)

    test_question = "Вопрос"
    test_answer = "Ответ"
    test_confluence_url = "confluence.com"

    def test_add_get_user(self):
        """Тест добавления и получения пользователя по id"""

        is_added, id = add_user(self.engine, 1, None)
        assert is_added is True
        assert id == get_user_id(self.engine, 1, None)
        is_added, id = add_user(self.engine, 1, None)
        assert is_added is False
        assert id == get_user_id(self.engine, 1, None)
        is_added, id = add_user(self.engine, None, 1)
        assert is_added is True
        assert id == get_user_id(self.engine, None, 1)
        is_added, id = add_user(self.engine, None, 1)
        assert is_added is False
        assert id == get_user_id(self.engine, None, 1)
        with pytest.raises(Exception):
            add_user(self.engine, None, None)
        assert get_user_id(self.engine, 2, None) is None
        assert get_user_id(self.engine, None, 2) is None
        with pytest.raises(Exception):
            get_user_id(self.engine, None, None)

    def test_subscribing(self):
        """Тест оформления подписки пользователя на рассылку"""

        user_id = get_user_id(self.engine, 1, None)
        assert user_id is not None
        assert check_subscribing(self.engine, user_id) is True
        assert subscribe_user(self.engine, user_id) is False
        assert check_subscribing(self.engine, user_id) is False
        assert subscribe_user(self.engine, user_id) is True
        assert check_subscribing(self.engine, user_id) is True

    def test_get_subscribed_users(self):
        """Тест получения списков подписанных пользователей"""

        _, user_id = add_user(self.engine, 10, None)
        assert check_subscribing(self.engine, user_id) is True
        _, user_id = add_user(self.engine, 20, None)
        assert check_subscribing(self.engine, user_id) is True
        _, user_id = add_user(self.engine, 30, None)
        assert subscribe_user(self.engine, user_id) is False
        assert check_subscribing(self.engine, user_id) is False
        _, user_id = add_user(self.engine, None, 100)
        assert check_subscribing(self.engine, user_id) is True
        _, user_id = add_user(self.engine, None, 200)
        assert check_subscribing(self.engine, user_id) is True
        _, user_id = add_user(self.engine, None, 300)
        assert subscribe_user(self.engine, user_id) is False
        assert check_subscribing(self.engine, user_id) is False
        vk_users, tg_users = get_subscribed_users(self.engine)
        assert 10 in vk_users
        assert 20 in vk_users
        assert 30 not in vk_users
        assert 100 in tg_users
        assert 200 in tg_users
        assert 300 not in tg_users

    def test_rate_answer(self):
        """Тест функции оценивания ответа"""

        user_id = get_user_id(self.engine, 1, None)
        assert user_id is not None
        answer_id = add_question_answer(
            self.engine,
            self.test_question,
            self.test_answer,
            self.test_confluence_url,
            user_id,
        )
        assert answer_id is not None
        assert rate_answer(self.engine, answer_id, 1) == True
        with Session(self.engine) as session:
            answer = session.scalar(
                select(QuestionAnswer).where(QuestionAnswer.id == answer_id)
            )
            assert answer is not None
            assert answer.question == self.test_question
            assert answer.answer == self.test_answer
            assert answer.confluence_url == self.test_confluence_url
            assert answer.score == 1
            assert answer.user_id == user_id
        assert rate_answer(self.engine, answer_id, 5) == True
        with Session(self.engine) as session:
            answer = session.scalar(
                select(QuestionAnswer).where(QuestionAnswer.id == answer_id)
            )
            assert answer is not None
            assert answer.score == 5
        assert rate_answer(self.engine, 0, 5) == False

    def test_check_spam(self):
        """Тест функции, проверяющей спам"""

        user_id = get_user_id(self.engine, 1, None)
        assert user_id is not None
        assert check_spam(self.engine, user_id) is False
        with Session(self.engine) as session:
            for _ in range(6):
                session.add(
                    QuestionAnswer(
                        question=self.test_question,
                        answer=self.test_answer,
                        user_id=user_id,
                    )
                )
            session.commit()
        assert check_spam(self.engine, user_id) is True
        with Session(self.engine) as session:
            for qa in session.execute(
                select(QuestionAnswer).where(QuestionAnswer.user_id == user_id)
            ).scalars():
                qa.created_at = qa.created_at.replace(year=2020)
            session.commit()
        assert check_spam(self.engine, user_id) is False
