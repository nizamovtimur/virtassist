import asyncio
import json
import math
import sys
import threading
import aiogram as tg
from atlassian import Confluence
from loguru import logger
from sqlalchemy import and_, create_engine, func, select
from sqlalchemy.orm import Session
import vkbottle as vk
from vkbottle.bot import Message as VKMessage
from vkbottle.http import aiohttp
from config import Config
from confluence_interaction import make_markup_by_confluence, parse_confluence_by_page_id
from database import User, QuestionAnswer
from strings import Strings


class Permission(vk.ABCRule[VKMessage]):
    def __init__(self, user_ids: list):
        self.uids = user_ids

    async def check(self, event: VKMessage):
        return event.from_id in self.uids


async def get_answer(question: str) -> tuple[str, int|None]:
    question = question.strip().lower()
    async with aiohttp.ClientSession() as session:
        async with session.post(f"http://{Config.QA_HOST}/qa/", json={"question": question}) as response:
            if response.status == 200:
                resp = await response.json()
                return resp["answer"], resp["confluence_id"]
            else:
                return ("", None)              


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
        vk.Keyboard()
        .add(vk.Text(Strings.ConfluenceButton))
        .row()
        .add(vk.Text(notify_text))
        .get_json()
    )


def tg_keyboard_choice(notify_text: str) -> tg.types.ReplyKeyboardMarkup:
    keyboard = tg.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(tg.types.KeyboardButton(Strings.ConfluenceButton))
    keyboard.add(tg.types.KeyboardButton(notify_text))
    return keyboard


engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
confluence = Confluence(url=Config.CONFLUENCE_HOST, token=Config.CONFLUENCE_TOKEN)
confluence_main_space = Config.CONFLUENCE_SPACES[0]
vk_bot = vk.Bot(token=Config.VK_ACCESS_GROUP_TOKEN)
vk_bot.labeler.vbml_ignore_case = True
vk_bot.labeler.custom_rules["permission"] = Permission
tg_bot = tg.Bot(token=Config.TG_ACCESS_TOKEN)
dispatcher = tg.Dispatcher(tg_bot)
        

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
        users_with_answers_count = session.scalar(select(func.count(User.id)).where(User.question_answers.any()))
        answers_count = session.scalar(select(func.count(QuestionAnswer.id)))
        scores_avg = session.scalar(select(func.avg(QuestionAnswer.score)))
        await message.answer(
            message=f"Количество пользователей: {users_count}\n"
                    f"Количество пользователей, получивших ответ: {users_with_answers_count}\n\n"
                    f"Количество вопросов: {answers_count}\n"
                    f"Средняя оценка: {scores_avg}", random_id=0)


async def vk_send_confluence_keyboard(message: VKMessage, question_types: list):
    keyboards = [vk.Keyboard(inline=True) for _ in range(math.ceil(len(question_types) / 5))]
    for i in range(len(question_types)):
        keyboards[i // 5].row()
        keyboards[i // 5].add(vk.Text(question_types[i]['content']['title'] if len(question_types[i]['content']['title']) < 40 
                                        else question_types[i]['content']['title'][:37]+"...", 
                                        payload={"conf_id": int(question_types[i]['content']['id'])}))
    keyboard_message = Strings.WhichInfoDoYouWant
    for i in range(len(keyboards)):
        await message.answer(
            message=keyboard_message,
            keyboard=keyboards[i].get_json(),
            random_id=0
        )
        keyboard_message = "⠀"
        
        
async def tg_send_confluence_keyboard(message: tg.types.Message, question_types: list):
    inline_keyboard = tg.types.InlineKeyboardMarkup()
    for i in question_types:
        inline_keyboard.add(tg.types.InlineKeyboardButton(text=i['content']['title'], 
                                                            callback_data=f"conf_id{i['content']['id']}"))
    await message.answer(
        text=Strings.WhichInfoDoYouWant,
        reply_markup=inline_keyboard
    )
    

@vk_bot.on.message(text=[Strings.ConfluenceButton])
async def vk_handler(message: VKMessage):
    question_types = make_markup_by_confluence(confluence, confluence_main_space)
    await vk_send_confluence_keyboard(message, question_types)
    

@dispatcher.message_handler(text=[Strings.ConfluenceButton])
async def tg_handler(message: tg.types.Message):
    question_types = make_markup_by_confluence(confluence, confluence_main_space)
    await tg_send_confluence_keyboard(message, question_types)


@vk_bot.on.message(func=lambda message: "conf_id" in message.payload if message.payload is not None else False)
async def vk_confluence_parse(message: VKMessage):
    id = json.loads(message.payload)["conf_id"]
    parse = parse_confluence_by_page_id(confluence, id)
    if type(parse) == list:
        await vk_send_confluence_keyboard(message, parse)
    elif type(parse) == str:
        await message.answer(
            message=parse,
            random_id=0
        )


@dispatcher.callback_query_handler(lambda c: c.data.startswith("conf_id"))
async def tg_confluence_parse(callback: tg.types.CallbackQuery):
    parse = parse_confluence_by_page_id(confluence, callback.data[7:])
    if type(parse) == list:
        await tg_send_confluence_keyboard(callback.message, parse)
    elif type(parse) == str:
        await callback.message.answer(text=parse)

     
@vk_bot.on.message(payload=[{"score": i} for i in range(1, 6)])
async def vk_rate(message: VKMessage):
    with Session(engine) as session:
        user = session.scalars(select(User).where(User.vk_id == message.from_id)).first()
        if user is None:
            return
        question_answer = session.scalars(select(QuestionAnswer)
                                   .where(and_(QuestionAnswer.user_id == user.id, 
                                               QuestionAnswer.confluence_id != None))
                                   .order_by(QuestionAnswer.id.desc())).first()
        if question_answer is None:
            return
        question_answer.score = json.loads(message.payload)["score"]
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
        question_answer = session.scalars(select(QuestionAnswer)
                                   .where(and_(QuestionAnswer.user_id == user.id, 
                                               QuestionAnswer.confluence_id != None))
                                   .order_by(QuestionAnswer.id.desc())).first()
        if question_answer is None:
            return
        question_answer.score = int(callback_query.data)
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
    answer, confluence_id = await get_answer(message.text)
    await vk_bot.api.messages.delete(message_ids=[processing.message_id], peer_id=message.peer_id, delete_for_all=True)
    
    with Session(engine) as session:
        user = session.scalars(select(User).where(User.vk_id == message.from_id)).first()
        if user is not None:
            question_answer = QuestionAnswer(
                question=message.text,
                answer=answer,
                confluence_id=confluence_id,
                user=user
            )
            session.add(question_answer)
            session.commit()     
    
    if confluence_id is None:
        await message.answer(
            message=Strings.NotFound,
            keyboard=vk_keyboard_choice(notify_text), random_id=0)
    else:
        if len(answer) == 0:
            answer = Strings.NotAnswer
        await message.answer(
        message=f"{answer}\n\n{Strings.SourceURL} {Config.CONFLUENCE_HOST}/pages/viewpage.action?pageId={confluence_id}",
        keyboard=vk_keyboard_choice(notify_text), random_id=0)
        await message.answer(
        message=Strings.RateAnswer,
        keyboard=(
            vk.Keyboard(inline=True).add(vk.Text("👎", payload={"score": 1}))
            # .add(vk.Text("2", payload={"score": 2}))
            # .add(vk.Text("3", payload={"score": 3}))
            # .add(vk.Text("4", payload={"score": 4}))
            .add(vk.Text("👍", payload={"score": 5}))
        ), random_id=0)


@dispatcher.message_handler(commands=['start'])
async def tg_start(message: tg.types.Message):
    add_user(telegram_id=message['from']['id'])
    notify_text = Strings.Unsubscribe if check_subscribing(telegram_id=message['from']['id']) else Strings.Subscribe
    await message.answer(
        text=Strings.FirstMessage,
        reply_markup=tg_keyboard_choice(notify_text)
    )


@dispatcher.message_handler()
async def tg_answer(message: tg.types.Message):
    if len(message['text']) > 1:
        processing = await message.answer(Strings.TryFindAnswer)
        answer, confluence_id = await get_answer(message["text"])
        await tg_bot.delete_message(message['chat']['id'], processing['message_id'])
        
        with Session(engine) as session:
            user = session.scalars(select(User).where(User.telegram_id  == message['from']['id'])).first()
            if user is not None:
                question_answer = QuestionAnswer(
                    question=message["text"],
                    answer=answer,
                    confluence_id=confluence_id,
                    user=user
                )
                session.add(question_answer)
                session.commit()  
        
        if confluence_id is None:
            await message.answer(text=Strings.NotFound)
        else:
            if len(answer) == 0:
                answer = Strings.NotAnswer
            await message.answer(
                text=f"{answer}\n\n{Strings.SourceURL} {Config.CONFLUENCE_HOST}/pages/viewpage.action?pageId={confluence_id}")
            await message.answer(
            text=Strings.RateAnswer,
            reply_markup=tg.types.InlineKeyboardMarkup().add(
                tg.types.InlineKeyboardButton(text="👎", callback_data="1"),
                # tg.types.InlineKeyboardButton(text="2", callback_data="2"),
                # tg.types.InlineKeyboardButton(text="3", callback_data="3"),
                # tg.types.InlineKeyboardButton(text="4", callback_data="4"),
                tg.types.InlineKeyboardButton(text="👍", callback_data="5")
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
