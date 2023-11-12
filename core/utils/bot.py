from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import InlineKeyboardMarkup

import database as db
from core.config import config


async def notify_user(
    user_id: int,
    bot: Bot | int,
    message: str,
    reply_markup: InlineKeyboardMarkup,
):
    close_after_notification = False
    if not isinstance(bot, Bot):
        bot = await get_bot_by_id(bot)
        close_after_notification = True

    await bot.send_message(
        chat_id=user_id,
        text=message,
        reply_markup=reply_markup,
    )

    if close_after_notification:
        await bot.session.close()


async def get_bot_username(bot: Bot) -> str:
    return (await bot.get_me()).username


def get_bot_by_id(bot_id: int) -> Bot:
    token = db.get_bot_token_by_id(bot_id)

    if token is None:
        token = config.BOT_TOKEN

    return Bot(token=token, session=AiohttpSession())
