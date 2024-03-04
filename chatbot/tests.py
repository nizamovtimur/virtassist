from confluence_interaction import make_markup_by_confluence, parse_confluence_by_page_id
from database import User, QuestionAnswer, Base
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from main import add_user, check_subscribing, check_spam, rate_answer
import pytest


def test_make_markup_by_confluence():
    assert type(make_markup_by_confluence()) is list
    assert len(make_markup_by_confluence()) > 0


def test_parse_confluence_by_page_id():
    markup = make_markup_by_confluence()
    for i in markup:
        assert type(parse_confluence_by_page_id(i['content']['id'])) in [list, str]
        assert len(parse_confluence_by_page_id(i['content']['id'])) > 0
    with pytest.raises(Exception):
        parse_confluence_by_page_id(0)
   

def test_db_functions():
    engine = create_engine('sqlite://', echo=True)
    Base.metadata.create_all(engine)
    assert add_user(engine, 1, None) is True
    assert add_user(engine, None, 1) is True
    assert add_user(engine, 1, None) is False
    assert add_user(engine, None, 1) is False
    assert check_subscribing(engine, vk_id = 1) is True
    assert check_subscribing(engine, telegram_id = 1) is True
    with pytest.raises(Exception):
        add_user(engine, None, None)
    with pytest.raises(Exception):
        check_subscribing(engine, None, None)
    assert check_subscribing(engine, vk_id = 2) is False
    assert check_subscribing(engine, telegram_id = 2) is False
    assert add_user(engine, 2, None) is True
    assert add_user(engine, None, 2) is True
    with Session(engine) as session:
        user1 = session.scalar(select(User).where(User.vk_id == 2))
        user2 = session.scalar(select(User).where(User.telegram_id == 2))
        user1.is_subscribed = False
        user2.is_subscribed = False
        session.commit()
        assert check_subscribing(engine, vk_id = 2) is False
        assert check_subscribing(engine, telegram_id = 2) is False
        user1.is_subscribed = True
        user2.is_subscribed = True
        session.commit()
        assert check_subscribing(engine, vk_id = 2) is True
        assert check_subscribing(engine, telegram_id = 2) is True
        question_answer = QuestionAnswer(
        question='Вопрос',
        answer='Ответ',
        user=user1
        )
        session.add(question_answer)
        session.flush()
        session.refresh(question_answer)
        session.commit()
        rate_answer(engine, 1, question_answer_id=question_answer.id)
        session.commit()
        question_answer = session.scalars(select(QuestionAnswer).where(QuestionAnswer.id == question_answer.id)).first()
        assert question_answer.score == 1
        rate_answer(engine, 5, question_answer_id=question_answer.id)
        session.commit()
        question_answer = session.scalars(select(QuestionAnswer).where(QuestionAnswer.id == question_answer.id)).first()
        assert question_answer.score == 5
        assert check_spam(engine, user1.vk_id, user1.telegram_id) == False
        question_answer = QuestionAnswer(
        question='Вопрос',
        answer='Ответ',
        user=user2
        )
        session.add(question_answer)
        session.flush()
        session.refresh(question_answer)
        session.commit()
        assert check_spam(engine, user2.vk_id, user2.telegram_id) == False
        question_answer = QuestionAnswer(
        question='Вопрос',
        answer='Ответ',
        user=user2
        )
        session.add(question_answer)
        session.flush()
        session.refresh(question_answer)
        session.commit()
        assert check_spam(engine, user2.vk_id, user2.telegram_id) == False
        question_answer = QuestionAnswer(
        question='Вопрос',
        answer='Ответ',
        user=user2
        )
        session.add(question_answer)
        session.flush()
        session.refresh(question_answer)
        session.commit()
        assert check_spam(engine, user2.vk_id, user2.telegram_id) == False
        question_answer = QuestionAnswer(
        question='Вопрос',
        answer='Ответ',
        user=user2
        )
        session.add(question_answer)
        session.flush()
        session.refresh(question_answer)
        session.commit()
        print(question_answer.time_created)
        assert check_spam(engine, user2.vk_id, user2.telegram_id) == True
        with pytest.raises(Exception):
            check_spam(engine, None, None)
