import asyncio
import logging
import os
import random
import string
import sys
from os import getenv
from main import client
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.utils.markdown import hbold

# Bot token can be obtained via https://t.me/BotFather
TOKEN = getenv("BOT_TOKEN")

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    # Most event objects have aliases for API methods that can be called in events' context
    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
    # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
    # method automatically or call API method directly via
    # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
    await message.answer(f"Hello, {hbold(message.from_user.full_name)}!")


@dp.message(Command('my_urls'))
async def my_urls_handler(message: Message) -> None:
    """
    This handler receives messages with `/my_urls` command
    """
    db = client["url_shortener"]
    collection = db["urls"]
    await message.answer(f"Your urls: ")
    user_urls = collection.find({"user_id": message.from_user.id})
    async for url_data in user_urls:
        await message.answer(
            f"{url_data.get('short_url')} >>> {url_data.get('long_url')} count: {url_data.get('count', 0)}")


@dp.message()
async def echo_handler(message: types.Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    db = client["url_shortener"]
    collection = db["urls"]
    try:
        # Send a copy of the received message
        bot_answer = 'Invalid url'
        if message.text.lower().startswith("http://") or message.text.lower().startswith("https://"):
            short_url = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(4))
            await collection.insert_one(
                {"short_url": short_url, "long_url": message.text, "user_id": message.from_user.id})
            bot_answer = short_url
        else:
            doc_with_long_url = await collection.find_one({"short_url": message.text})
            if doc_with_long_url is not None:
                long_url = doc_with_long_url.get("long_url")
                if long_url:
                    bot_answer = long_url
        await message.answer(bot_answer)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Nice try!")


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
