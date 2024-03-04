import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from database import Base, QuestionAnswer, add_user, get_user_id, subscribe_user, check_subscribing, check_spam, add_question_answer, rate_answer


class TestDBFunctions:
    engine = create_engine("sqlite://", echo=True)
    Base.metadata.create_all(engine)
    
    def test_add_get_user(self):
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
        user_id = get_user_id(self.engine, 1, None)
        assert user_id is not None
        assert check_subscribing(self.engine, user_id) is True
        assert subscribe_user(self.engine, user_id) is False
        assert check_subscribing(self.engine, user_id) is False
        assert subscribe_user(self.engine, user_id) is True
        assert check_subscribing(self.engine, user_id) is True
    
    def test_rate_answer(self):
        user_id = get_user_id(self.engine, 1, None)
        assert user_id is not None
        answer_id = add_question_answer(self.engine, "Вопрос", "Ответ", "confluence.com", user_id)
        assert answer_id is not None
        rate_answer(self.engine, answer_id, 1)
        with Session(self.engine) as session:
            answer = session.scalar(select(QuestionAnswer).where(QuestionAnswer.id == answer_id))
            assert answer is not None
            assert answer.question == "Вопрос"
            assert answer.answer == "Ответ"
            assert answer.confluence_url == "confluence.com"
            assert answer.score == 1
            assert answer.user_id == user_id
        rate_answer(self.engine, answer_id, 5)
        with Session(self.engine) as session:
            answer = session.scalar(select(QuestionAnswer).where(QuestionAnswer.id == answer_id))
            assert answer is not None
            assert answer.score == 5
    
    def test_check_spam(self):
        user_id = get_user_id(self.engine, 1, None)
        assert user_id is not None
        assert check_spam(self.engine, user_id) is False
        with Session(self.engine) as session:
            for _ in range(4):
                session.add(QuestionAnswer(question="Вопрос", answer="Ответ", user_id=user_id))
            session.commit()
        assert check_spam(self.engine, user_id) is True
        with Session(self.engine) as session:
            for qa in session.execute(select(QuestionAnswer).where(QuestionAnswer.user_id == user_id)).scalars():
                qa.time_created = qa.time_created.replace(year=2020)
            session.commit()
        assert check_spam(self.engine, user_id) is False
