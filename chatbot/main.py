import sys
from loguru import logger
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from vkbottle import Bot, Keyboard, Text, ABCRule
from vkbottle.bot import Message
from vkbottle.dispatch.rules.base import RegexRule
from config import Config
from database import User, Question


class Permission(ABCRule[Message]):
    def __init__(self, user_ids):
        if not isinstance(user_ids, list):
            user_ids = [user_ids]
        self.uids = user_ids

    async def check(self, event: Message):
        return event.from_id in self.uids


engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
bot = Bot(token=Config.ACCESS_GROUP_TOKEN)
bot.labeler.vbml_ignore_case = True
bot.labeler.custom_rules["permission"] = Permission


@bot.on.message(RegexRule("!send "), permission=Config.SUPERUSER_VK_ID)
async def handler(message: Message):
    with Session(engine) as session:
        for _user in session.scalars(select(User)):
            if _user.is_subscribed:
                try:
                    await bot.api.messages.send(user_id=_user.id, message=message.text[6:], random_id=0)
                except Exception as e:
                    print(e)


def add_user(user_id):
    with Session(engine) as session:
        user = User(id=user_id, dialog_iteration=0, is_subscribed=1)
        session.merge(user)
        session.commit()


def user_increment_iteration(user_id):
    with Session(engine) as session:
        user = session.scalar(select(User).where(User.id == user_id))
        user.dialog_iteration += 1
        session.commit()
        return user.dialog_iteration


# def check_subscribing(user_id):
#     with Session(engine) as session:
#         user = session.scalar(select(User).where(User.id == user_id))
#         if user is None:
#             return True
#         return user.is_subscribed


# def main_keyboard_choice(notify_text):
#     return (
#         Keyboard().add(Text(notify_text))
#         .get_json()
#     )


@bot.on.message(text=["начать", "start"])
async def handler(message: Message):
    add_user(message.from_id)
    # is_user_subscribed = check_subscribing(message.from_id)
    # notify_text = "Отписаться от рассылки" if is_user_subscribed else "Подписаться на рассылку"
    intro_message = f"👋🏻 Привет! Я виртуальный помощник ТюмГУ и я только учусь помогать студентам находить ответы на вопросы. " \
                     f"В будущем я смогу отвечать на вопросы, касающиеся нашего университета, а пока что мне нужна твоя помощь. " \
                      f"Можешь рассказать, какие вопросы у тебя возникали за время обучения в ТюмГУ?\n\n" \
                    f"Продолжая работу с ботом, ты разрешаешь обработку своих персональных данных и получение сообщений."
    keyboard_choice = (
        Keyboard(inline=True).add(Text("Хочу рассказать о вопросах")).get_json()
    )
    await message.answer(
        message=intro_message,
        keyboard=keyboard_choice, random_id=0)


@bot.on.message(text=["хочу рассказать о вопросах", "хочу ещё рассказать о вопросах"])
async def handler(message: Message):
    dialog_iteration = user_increment_iteration(message.from_id)
    if dialog_iteration == 6:
        with Session(engine) as session:
            user = session.scalars(select(User).where(User.id == message.from_id)).first()
            dialog_iteration = 1
            user.dialog_iteration = dialog_iteration
            session.commit()
    if dialog_iteration == 1:
        await message.answer(
            message="Расскажи, пожалуйста, какой вопрос у тебя возник?", random_id=0)


@bot.on.message(text=["больше вопросов не было"])
async def handler(message: Message):
    dialog_iteration = user_increment_iteration(message.from_id)
    if dialog_iteration == 6:
        await message.answer(message="Превосходно!", random_id=0)
        with Session(engine) as session:
            user = session.scalars(select(User).where(User.id == message.from_id)).first()
            if user.experience is None:
                await message.answer(message="У меня есть к тебе ещё пара вопросов. Вот первый:\n\n"
                                             "Расскажи, пожалуйста, где ты обычно получаешь ответы на вопросы, "
                                             "возникающие в ходе обучения в ТюмГУ?", random_id=0)
            else:
                user.dialog_iteration += 1
                session.commit()
                if user.fantasies is None:
                    await message.answer(
                        message="У меня к тебе есть вопрос. Какими, на твой взгляд, функциями должен обладать"
                                " виртуальный помощник студента в идеале"
                                " и важна ли человеко-подобность ответов как у ChatGPT?",
                        random_id=0)


@bot.on.message()
async def handler(message: Message):
    if len(message.text) < 3:
        await message.answer(
            message="Твой ответ меньше трёх символов, попробуй ещё раз", random_id=0)
        return
    dialog_iteration = user_increment_iteration(message.from_id)
    if dialog_iteration == 1:
        with Session(engine) as session:
            user = session.scalars(select(User).where(User.id == message.from_id)).first()
            user.dialog_iteration = 0
            session.commit()
    if dialog_iteration == 2:
        question = Question(question=message.text, user_id=message.from_id)
        with Session(engine) as session:
            session.add(question)
            session.commit()
        await message.answer(
            message="Какой ответ тебе дали?", random_id=0)
    if dialog_iteration == 3:
        with Session(engine) as session:
            question = session.scalars(select(Question).where(Question.user_id == message.from_id).order_by(
                Question.id.desc()).limit(1)).first()
            question.answer = message.text
            session.commit()
        await message.answer(
            message="Кто тебе ответил на вопрос?", random_id=0)
    if dialog_iteration == 4:
        with Session(engine) as session:
            question = session.scalars(select(Question).where(Question.user_id == message.from_id).order_by(
                Question.id.desc()).limit(1)).first()
            question.department = message.text
            session.commit()
        keyboard_choice = (
            Keyboard(inline=True).add(Text("Отлично")).row()
            .add(Text("Хорошо")).row()
            .add(Text("Удовлетворительно")).row()
            .add(Text("Плохо")).row()
            .add(Text("Ужасно")).get_json()
        )
        await message.answer(
            message="Как ты оцениваешь ответ?",
            keyboard=keyboard_choice, random_id=0)
    if dialog_iteration == 5:
        with Session(engine) as session:
            question = session.scalars(select(Question).where(Question.user_id == message.from_id).order_by(
                Question.id.desc()).limit(1)).first()
            question.score = message.text
            session.commit()
        keyboard_choice = (
            Keyboard(inline=True).add(Text("Хочу ещё рассказать о вопросах")).row()
            .add(Text("Больше вопросов не было")).get_json()
        )
        await message.answer(
            message="Хочешь ли ещё рассказать о вопросах, которые у тебя возникали?",
            keyboard=keyboard_choice, random_id=0)
    if dialog_iteration == 7:
        with Session(engine) as session:
            user = session.scalars(select(User).where(User.id == message.from_id)).first()
            user.experience = message.text
            if user.fantasies is None:
                await message.answer(
                    message="Отлично! Вот мой последний вопрос:\n\n"
                            "Какими, на твой взгляд, функциями должен обладать виртуальный помощник студента в идеале"
                            " и важна ли человеко-подобность ответов как у ChatGPT?",
                    random_id=0)
            else:
                user.dialog_iteration += 1
            session.commit()
    if dialog_iteration == 8:
        with Session(engine) as session:
            user = session.scalars(select(User).where(User.id == message.from_id)).first()
            user.fantasies = message.text
            session.commit()
        await message.answer(
            message="Большое спасибо! 🤗", random_id=0)
        await message.answer(
            message="Если у тебя появится чем ещё поделиться, напиши «начать». "
                    "Хочешь следить за моим прогрессом? Подписывайся @public222974741 (на мой паблик) 😉", random_id=0)


# @bot.on.message(text=["уведомления", "отписаться от рассылки", "подписаться на рассылку"])
# async def handler(message: Message):
#     with Session(engine) as session:
#         user = session.scalars(select(User).where(User.id == message.from_id)).first()
#         user.is_subscribed = not user.is_subscribed
#         session.commit()
#         notify_text = "Отписаться от рассылки" if user.is_subscribed else "Подписаться на рассылку"
#         await message.answer(
#             message="Теперь ты будешь получать уведомления от чат-бота 🎉" if user.is_subscribed
#             else "Тебе больше не будут приходить уведомления от чат-бота 😢",
#             keyboard=main_keyboard_choice(notify_text), random_id=0)


if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    bot.run_forever()
