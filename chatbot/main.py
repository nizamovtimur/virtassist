import asyncio
import json
import sys
import threading
import aiogram as tg
from loguru import logger
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import and_, create_engine, func, select, text
from sqlalchemy.orm import Session
import vkbottle as vk
from vkbottle.bot import Message as VKMessage
from vkbottle.http import aiohttp
from config import Config
from database import User, Answer, Question
from strings import Strings
from confluence_interaction import ConfluenceInteraction

class Permission(vk.ABCRule[VKMessage]):
    def __init__(self, user_ids: list):
        self.uids = user_ids

    async def check(self, event: VKMessage):
        return event.from_id in self.uids


async def get_answer(question: str, vk_id: int|None = None, telegram_id: int|None = None) -> tuple[str, list[str]]:
    question = question.strip().lower()
    similar_questions = []
    async with aiohttp.ClientSession() as session:
        async with session.post(f"http://{Config.QA_HOST}/", json={"question": question}) as response:
            answer = await response.text()
    with Session(engine) as session:
        if vk_id is not None:
            user = session.scalars(select(User).where(User.vk_id == vk_id)).first()
        elif telegram_id is not None:
            user = session.scalars(select(User).where(User.telegram_id == telegram_id)).first()
        else:
            raise Exception("vk_id and telegram_id can't be None at the same time")
        if user is not None:
            question_db = session.scalars(select(Question).where(Question.text == question)).first()
            if question_db is None:
                question_db = Question(text=question, embedding=vector_model.encode(question))
                session.add(question_db)
            embedding = question_db.embedding
            answer_db = Answer(text=answer, user=user, question=question_db)
            session.add(answer_db)
            # TODO: questions filtration
            if len(answer) == 0 and vk_id in Config.VK_SUPERUSER_ID:
                similar_questions_sql = session.execute(
                    text(f"""SELECT text
FROM question
WHERE id != :q_id
    AND (
        SELECT AVG(score)
        FROM answer
        WHERE question_id = question.id
    ) > 3
ORDER BY embedding <=> :q_embedding
LIMIT 3""").bindparams(q_id=0 if question_db.id is None else question_db.id, q_embedding=np.array2string(np.array(embedding), separator=','))).scalars()
                similar_questions = [str(sq) for sq in similar_questions_sql]
            session.commit()     

    return answer, similar_questions            


def add_user(vk_id: int|None = None, telegram_id: int|None = None) -> bool:
    with Session(engine) as session:
        if vk_id is not None:
            user = session.scalar(select(User).where(User.vk_id == vk_id))
        elif telegram_id is not None:
            user = session.scalar(select(User).where(User.telegram_id == telegram_id))
        else:
            raise Exception("vk_id and telegram_id can't be None at the same time")
        if user is None:
            user = User(vk_id=vk_id, telegram_id=telegram_id, is_subscribed=True)
            session.add(user)
            session.commit()
            return True
        return False


def check_subscribing(vk_id: int|None = None, telegram_id: int|None = None) -> bool:
    with Session(engine) as session:
        if vk_id is not None:
            user = session.scalar(select(User).where(User.vk_id == vk_id))
        elif telegram_id is not None:
            user = session.scalar(select(User).where(User.telegram_id == telegram_id))
        else:
            raise Exception("vk_id and telegram_id can't be None at the same time")
        if user is None:
            return False
        return user.is_subscribed


def vk_keyboard_choice(notify_text: str) -> str:
    return (
        vk.Keyboard().add(vk.Text(notify_text)).row().add(vk.Text('Руководства и инструкции', payload={"command": 1}))
        .get_json()
    )


def tg_keyboard_choice(notify_text: str) -> tg.types.ReplyKeyboardMarkup:
    keyboard = tg.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(tg.types.KeyboardButton(notify_text))
    keyboard.add(tg.types.KeyboardButton('Руководства и инструкции для обучающихся'))
    return keyboard


engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
vk_bot = vk.Bot(token=Config.VK_ACCESS_GROUP_TOKEN)
vk_bot.labeler.vbml_ignore_case = True
vk_bot.labeler.custom_rules["permission"] = Permission
tg_bot = tg.Bot(token=Config.TG_ACCESS_TOKEN)
dispatcher = tg.Dispatcher(tg_bot)
vector_model = SentenceTransformer('saved_models/rubert-tiny2-retriever')    
        

# TODO: move to web admin panel
@vk_bot.on.message(vk.dispatch.rules.base.RegexRule("!send "), permission=Config.VK_SUPERUSER_ID)
async def vk_deliver_notifications(message: VKMessage):
    with Session(engine) as session:
        for user in session.execute(select(User).where(and_(User.vk_id != None, User.is_subscribed))).scalars():
            try:
                await vk_bot.api.messages.send(user_id=user.vk_id, message=message.text[6:], random_id=0)
            except Exception as e:
                logger.error(e)


# TODO: move to web admin panel
@vk_bot.on.message(text=["stats"], permission=Config.VK_SUPERUSER_ID)
async def vk_send_stats(message: VKMessage):
    with Session(engine) as session:
        users_count = session.scalar(select(func.count(User.id)))
        users_with_answers_count = session.scalar(select(func.count(User.id)).where(User.answers.any()))
        answers_count = session.scalar(select(func.count(Answer.id)))
        scores_avg = session.scalar(select(func.avg(Answer.score)))
        await message.answer(
            message=f"Количество пользователей: {users_count}\n"
                    f"Количество пользователей, получивших ответ: {users_with_answers_count}\n\n"
                    f"Количество ответов: {answers_count}\n"
                    f"Средняя оценка: {scores_avg}", random_id=0)


@vk_bot.on.message(payload=[{"score": i} for i in range(1, 6)])
async def vk_rate(message: VKMessage):
    with Session(engine) as session:
        user = session.scalars(select(User).where(User.vk_id == message.from_id)).first()
        if user is None:
            return
        answer = session.scalars(select(Answer)
                                   .where(and_(Answer.user_id == user.id, func.char_length(Answer.text) > 0))
                                   .order_by(Answer.id.desc())).first()
        if answer is None:
            return
        answer.score = json.loads(message.payload)["score"]
        session.commit()
    await message.answer(
        message=Strings.ThanksForFeedback,
        random_id=0)


@dispatcher.callback_query_handler()
async def tg_rate(callback_query: tg.types.CallbackQuery):
    with Session(engine) as session:
        user = session.scalars(select(User).where(User.telegram_id == callback_query['from']['id'])).first()
        if user is None:
            return
        answer = session.scalars(select(Answer)
                                   .where(and_(Answer.user_id == user.id, func.char_length(Answer.text) > 0))
                                   .order_by(Answer.id.desc())).first()
        if answer is None:
            return
        answer.score = int(callback_query.data)
        session.commit()
    await callback_query.answer(text=Strings.ThanksForFeedback)
    

@vk_bot.on.message(text=[Strings.Subscribe, Strings.Unsubscribe])
async def vk_subscribe(message: VKMessage):
    with Session(engine) as session:
        user = session.scalars(select(User).where(User.vk_id == message.from_id)).first()
        if user is None:
            return
        user.is_subscribed = not user.is_subscribed
        session.commit()
        notify_text = Strings.Unsubscribe if user.is_subscribed else Strings.Subscribe
        await message.answer(
            message=Strings.SubscribeMessage if user.is_subscribed
            else Strings.UnsubscribeMessage,
            keyboard=vk_keyboard_choice(notify_text), random_id=0)

@vk_bot.on.message(payload=[{"command": 1}])
async def vk_handler(message: VKMessage):
    inline_keyboard = vk.Keyboard(inline=True)
    inline_keyboards = []
    question_types = ConfluenceInteraction.make_markup_by_confluence()
    inline_keyboards.append(inline_keyboard)
    if len(question_types):
        for i in question_types:
            inline_keyboards[len(inline_keyboards) - 1].add(vk.Text(i, payload={"type": question_types[i]}))
            if len(inline_keyboards[len(inline_keyboards) - 1].buttons) == 5:
                inline_keyboards.append(vk.Keyboard(inline=True))
            elif sum([len(keyboard.buttons) for keyboard in inline_keyboards]) != len(question_types):
                inline_keyboards[len(inline_keyboards) - 1].row()
    for i in range(len(inline_keyboards)):
        await message.answer(
            message="Какую информацию хотите получить?",
            keyboard=inline_keyboards[i].get_json()
        )

@vk_bot.on.message(func=lambda message: type(json.loads(message.payload)['type']) == int)
async def confluence_parse(message: VKMessage):
    id = json.loads(message.payload)["type"]
    parse = ConfluenceInteraction.parse_confluence_by_page_id(id)
    if type(parse) == list:
        inline_keyboard = vk.Keyboard(inline=True)
        inline_keyboards = []
        inline_keyboards.append(inline_keyboard)
        for i in parse:
            inline_keyboards[len(inline_keyboards) - 1].add(vk.Text(i['title'], payload={"type": int(i['id'])}))
            if len(inline_keyboards[len(inline_keyboards) - 1].buttons) == 5:
                if sum([len(keyboard.buttons) for keyboard in inline_keyboards]) != len(parse):
                    inline_keyboards.append(vk.Keyboard(inline=True))
            elif sum([len(keyboard.buttons) for keyboard in inline_keyboards]) != len(parse):
                inline_keyboards[len(inline_keyboards) - 1].row()
        for i in range(len(inline_keyboards)):
            await message.answer(
                message="Какую информацию хотите получить?",
                keyboard=inline_keyboards[i].get_json()
            )
    else:
        await message.answer(
            message=parse
        )

@dispatcher.message_handler(text=[Strings.Subscribe, Strings.Unsubscribe])
async def tg_subscribe(message: tg.types.Message):
    with Session(engine) as session:
        user = session.scalars(select(User).where(User.telegram_id == message['from']['id'])).first()
        if user is None:
            return
        user.is_subscribed = not user.is_subscribed
        session.commit()
        notify_text = Strings.Unsubscribe if user.is_subscribed else Strings.Subscribe
        await message.reply(
            Strings.SubscribeMessage if user.is_subscribed
            else Strings.UnsubscribeMessage,
            reply_markup=tg_keyboard_choice(notify_text))


@vk_bot.on.message()
async def vk_answer(message: VKMessage):
    is_user_added = add_user(vk_id=message.from_id)
    notify_text = Strings.Unsubscribe if check_subscribing(vk_id=message.from_id) else Strings.Subscribe
    if is_user_added or Strings.Start in message.text.lower() or Strings.StartEnglish in message.text.lower():
        await message.answer(
            message=Strings.FirstMessage,
            keyboard=vk_keyboard_choice(notify_text), random_id=0)
        return
    
    processing = await message.answer(Strings.TryFindAnswer)
    answer, similar_questions = await get_answer(message.text, vk_id=message.from_id)
    await vk_bot.api.messages.delete(message_ids=[processing.message_id], peer_id=message.peer_id, delete_for_all=True)
    if len(similar_questions) > 0:
        await message.answer(
            message=Strings.NotFound + "\n\n" + "\n\n".join(similar_questions),
            keyboard=vk_keyboard_choice(notify_text), random_id=0)
    elif len(answer) == 0:
        await message.answer(
            message=Strings.NotFoundNotSimilar,
            keyboard=vk_keyboard_choice(notify_text), random_id=0)
    else:
        await message.answer(
        message=answer,
        keyboard=vk_keyboard_choice(notify_text), random_id=0)
        await message.answer(
        message=Strings.RateAnswer,
        keyboard=(
            vk.Keyboard(inline=True).add(vk.Text("1", payload={"score": 1}))
            .add(vk.Text("2", payload={"score": 2}))
            .add(vk.Text("3", payload={"score": 3}))
            .add(vk.Text("4", payload={"score": 4}))
            .add(vk.Text("5", payload={"score": 5}))
        ), random_id=0)


@dispatcher.message_handler(commands=['start'])
async def tg_start(message: tg.types.Message):
    add_user(telegram_id=message['from']['id'])
    notify_text = Strings.Unsubscribe if check_subscribing(telegram_id=message['from']['id']) else Strings.Subscribe
    await message.answer(
        text=Strings.FirstMessage,
        reply_markup=tg_keyboard_choice(notify_text)
    )

@dispatcher.callback_query_handler(lambda c: c.data.startswith('type'))
async def confluence_parse(callback: tg.types.CallbackQuery):
    id = int(callback.data[5:])
    parse = ConfluenceInteraction.parse_confluence_by_page_id(id)
    if type(parse) == list:
        inline_keyboard = tg.types.InlineKeyboardMarkup()
        for i in parse:
            inline_keyboard.add(tg.types.InlineKeyboardButton(text=i['title'], callback_data='type ' + str(i['id'])))
        await callback.message.answer(
            text="Какую информацию хотите получить?",
            reply_markup=inline_keyboard
        )
    else:
        await callback.message.answer(
            text=parse
        )

@dispatcher.message_handler(text=["Руководства и инструкции для обучающихся"])
async def telegram_handler(message: tg.types.Message):
    inline_keyboard = tg.types.InlineKeyboardMarkup()
    question_types = ConfluenceInteraction.make_markup_by_confluence()
    if len(question_types):
    	for i in question_types:
        	inline_keyboard.add(tg.types.InlineKeyboardButton(text=i, callback_data=question_types[i]))
    	await message.answer(
        	text="Какую информацию хотите получить?",
        	reply_markup=inline_keyboard
    	)

@dispatcher.message_handler()
async def tg_answer(message: tg.types.Message):
    if len(message['text']) > 1:
        processing = await message.answer(Strings.TryFindAnswer)
        answer, similar_questions = await get_answer(message["text"], telegram_id=message['from']['id'])
        await tg_bot.delete_message(message['chat']['id'], processing['message_id'])
        if len(similar_questions) > 0:
            await message.answer(text=Strings.NotFound + "\n\n" + "\n\n".join(similar_questions))
        elif len(answer) == 0:
            await message.answer(
                text=Strings.NotFoundNotSimilar)
        else:
            await message.answer(
                text=answer)
            await message.answer(
            text=Strings.RateAnswer,
            reply_markup=tg.types.InlineKeyboardMarkup().add(
                tg.types.InlineKeyboardButton(text="1", callback_data="1"),
                tg.types.InlineKeyboardButton(text="2", callback_data="2"),
                tg.types.InlineKeyboardButton(text="3", callback_data="3"),
                tg.types.InlineKeyboardButton(text="4", callback_data="4"),
                tg.types.InlineKeyboardButton(text="5", callback_data="5")
            ))


def launch_vk_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    vk_bot.run_forever()


def launch_telegram_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tg.executor.start_polling(dispatcher, skip_updates=True)


if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    thread_vk = threading.Thread(target=launch_vk_bot)
    thread_tg = threading.Thread(target=launch_telegram_bot)
    thread_tg.start()
    thread_vk.start()
    thread_tg.join()
    thread_vk.join()
