import json
import sys
from loguru import logger
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from vkbottle import Bot, Keyboard, Text, ABCRule
from vkbottle.bot import Message
from vkbottle.dispatch.rules.base import RegexRule
from vkbottle.http import aiohttp

from config import Config
from database import User, Question


class Permission(ABCRule[Message]):
    def __init__(self, user_ids: list):
        self.uids = user_ids

    async def check(self, event: Message):
        return event.from_id in self.uids


async def get_answer(question: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(Config.QA_HOST) as response:
            answer = await response.text()
            return answer[:15]


def add_user(user_id: int) -> bool:
    with Session(engine) as session:
        user = session.scalar(select(User).where(User.id == user_id))
        if user is None:
            user = User(id=user_id, is_subscribed=True)
            session.add(user)
            session.commit()
            return True
        return False


def check_subscribing(user_id: int) -> bool:
    with Session(engine) as session:
        user = session.scalar(select(User).where(User.id == user_id))
        if user is None:
            return False
        return user.is_subscribed


def main_keyboard_choice(notify_text: str) -> str:
    return (
        Keyboard().add(Text(notify_text))
        .get_json()
    )


engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
bot = Bot(token=Config.ACCESS_GROUP_TOKEN)
bot.labeler.vbml_ignore_case = True
bot.labeler.custom_rules["permission"] = Permission


@bot.on.message(RegexRule("!send "), permission=[Config.SUPERUSER_VK_ID])
async def handler(message: Message):
    with Session(engine) as session:
        for user in session.scalars(select(User).where(User.is_subscribed)).all():
            try:
                await bot.api.messages.send(user_id=user.id, message=message.text[6:], random_id=0)
            except Exception as e:
                print(e)


@bot.on.message(text=["stats"], permission=[Config.SUPERUSER_VK_ID])
async def handler(message: Message):
    with Session(engine) as session:
        users_count = session.scalar(select(func.count(User.id)))
        users_with_questions_count = session.scalar(select(func.count(User.id)).where(User.questions.any()))
        questions_count = session.scalar(select(func.count(Question.id)))
        scores_avg = session.scalar(select(func.avg(Question.score)))
        await message.answer(
            message=f"Количество пользователей: {users_count}\n"
                    f"Количество пользователей с вопросами: {users_with_questions_count}\n\n"
                    f"Количество вопросов: {questions_count}\n"
                    f"Средняя оценка: {scores_avg}", random_id=0)


@bot.on.message(payload=[{"score": i} for i in range(1, 6)])
async def handler(message: Message):
    with Session(engine) as session:
        question = session.scalars(select(Question)
                                   .where(Question.user_id == message.from_id and Question.score is None)
                                   .order_by(Question.id.desc())).first()
        question.score = json.loads(message.payload)["score"]
        session.commit()
    await message.answer(
        message=f"Спасибо за обратную связь! 🤗",
        random_id=0)


@bot.on.message(text=["отписаться", "отписаться от рассылки", "подписаться", "подписаться на рассылку"])
async def handler(message: Message):
    with Session(engine) as session:
        user = session.scalars(select(User).where(User.id == message.from_id)).first()
        user.is_subscribed = not user.is_subscribed
        session.commit()
        notify_text = "Отписаться от рассылки" if user.is_subscribed else "Подписаться на рассылку"
        await message.answer(
            message="Теперь ты будешь получать уведомления от чат-бота 🎉" if user.is_subscribed
            else "Тебе больше не будут приходить уведомления от чат-бота 😢",
            keyboard=main_keyboard_choice(notify_text), random_id=0)


@bot.on.message()
async def handler(message: Message):
    is_user_added = add_user(message.from_id)
    notify_text = "Отписаться от рассылки" if check_subscribing(message.from_id) else "Подписаться на рассылку"
    if is_user_added:
        first_message = f"👋🏻 Привет! Я виртуальный помощник ТюмГУ, сейчас я сформирую ответ на твой вопрос... \n\n" \
                        f"Продолжая работу, ты разрешаешь обработку своих персональных данных и получение сообщений. " \
                        f"Я также могу присылать тебе важные сообщения для всех студентов ТюмГУ, " \
                        f"однако ты можешь отписаться от рассылки."
        await message.answer(
            message=first_message,
            keyboard=main_keyboard_choice(notify_text), random_id=0)
    answer = await get_answer(message.text)
    await message.answer(
        message=answer,
        keyboard=main_keyboard_choice(notify_text), random_id=0)
    with Session(engine) as session:
        user = session.scalars(select(User).where(User.id == message.from_id)).first()
        question = Question(question=message.text, answer=answer, user_id=user.id)
        session.add(question)
        session.commit()
    await message.answer(
        message="Пожалуйста, оцени ответ по 5-балльной шкале, нажав одну из кнопок:",
        keyboard=(
            Keyboard(inline=True).add(Text("1", payload={"score": 1}))
            .add(Text("2", payload={"score": 2}))
            .add(Text("3", payload={"score": 3}))
            .add(Text("4", payload={"score": 4}))
            .add(Text("5", payload={"score": 5}))
        ), random_id=0)


if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    bot.run_forever()
