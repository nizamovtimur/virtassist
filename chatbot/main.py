import sys
from loguru import logger
from sqlalchemy import create_engine
from vkbottle import Bot
from vkbottle.bot import Message
from config import Config

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
bot = Bot(token=Config.ACCESS_GROUP_TOKEN)
bot.labeler.vbml_ignore_case = True


@bot.on.message(text=["начать", "start"])
async def handler(message: Message):
    await message.answer(
        message="Hello!", random_id=0)


if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    bot.run_forever()
