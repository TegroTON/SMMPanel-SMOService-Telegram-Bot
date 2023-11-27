import logging

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums.parse_mode import ParseMode
from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramNotFound,
    TelegramUnauthorizedError,
)
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.token import TokenValidationError, validate_token

import database as db
from core.config import config

logger = logging.getLogger(__name__)


async def notify_user(
    user_id: int,
    bot: Bot | int,
    message: str,
    reply_markup: InlineKeyboardMarkup,
):
    close_after_notification = False
    if not isinstance(bot, Bot):
        bot = get_bot_by_id(bot)
        close_after_notification = True
    try:
        await bot.send_message(
            chat_id=user_id,
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )
    except TelegramUnauthorizedError:
        logging.warning(f"Bot {bot.id} unauthorized!")
    except TelegramForbiddenError:
        logging.warning(f"User {user_id} blocked bot!")
    except TelegramNotFound:
        logging.warning(f"User {user_id} not found!")

    if close_after_notification:
        await bot.session.close()


async def get_bot_username(bot: Bot) -> str:
    return (await bot.get_me()).username


def get_bot_by_id(bot_id: int) -> Bot:
    token = db.get_bot_token_by_id(bot_id)

    if token is None:
        token = config.BOT_TOKEN

    return Bot(token=token, session=AiohttpSession())


def is_bot_token(value: str) -> bool:
    try:
        validate_token(value)
    except TokenValidationError:
        return False
    return True


def get_bot_id_by_token(token: str) -> int | None:
    bot_id = db.get_bot_id_by_token(token)

    if bot_id:
        return bot_id

    if token == config.BOT_TOKEN:
        return -1

    return None
