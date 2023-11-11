import logging
from typing import Any, Dict, Union

from aiogram import Bot, F, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.filters import StateFilter, or_f
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.token import TokenValidationError, validate_token

import database as db
import main
from core.callback_factories.my_bots import MyBotAction, MyBotCallbackData
from core.keyboards.my_bots import (
    create_delete_confirm_keyboard,
    create_manage_bot_keyboard,
    create_manage_bots_keyboard,
)
from core.keyboards.utils import create_back_keyboard
from core.utils.bot import get_bot_by_id, get_bot_username

logger = logging.getLogger(__name__)

NewBotRouter = Router()


class FSMFillFrom(StatesGroup):
    get_bot_token = State()


def is_bot_token(value: str) -> Union[bool, Dict[str, Any]]:
    try:
        validate_token(value)
    except TokenValidationError:
        return False
    return True


@NewBotRouter.callback_query(
    or_f(
        F.data == "my_bots",
        MyBotCallbackData.filter(F.action == MyBotAction.view_bots),
    )
)
async def my_bot_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await state.clear()

    bots_data = db.get_bots_for_user(callback.from_user.id)
    for bot_data in bots_data:
        try:
            bot = Bot(token=bot_data["api_key"], session=AiohttpSession())
            bot_info = await bot.get_me()
            bot_data["username"] = bot_info.username
        except TelegramUnauthorizedError as error:
            logger.error(error)
            logger.exception(error)
            bot_data["username"] = "Неавторизованный"
            continue
        finally:
            bot_data["current"] = False
            await bot.session.close()

        if bot_data["api_key"] == callback.bot.token:
            bot_data["current"] = True

    await callback.message.edit_text(
        text=(
            "<b>Управление ботами</b>\n"
            "Ваши боты помогают вам зарабатывать, каждый новый пользователь,"
            " который зарегистрируется через вашего бота, автоматически"
            " становится вашим рефералом.\n"
            "\n"
            "Здесь вы можете управлять своими ботами.\n"
            "Выберите бота или создайте нового.\n"
        ),
        reply_markup=create_manage_bots_keyboard(bots_data),
    )


@NewBotRouter.callback_query(
    MyBotCallbackData.filter(F.action == MyBotAction.view_bot),
)
async def view_bot_callback_handler(
    callback: CallbackQuery,
    callback_data: MyBotCallbackData,
):
    bot = get_bot_by_id(callback_data.bot_id)
    try:
        bot_info = await bot.get_me()
        text = (
            "<b>Информация о боте</b>\n\n"
            f"Имя: @{bot_info.username}\n\n"
            f"Токен: {bot.token}"
        )

    except TelegramUnauthorizedError:
        text = ("Токен недействителен.\n" f"Токен: {bot.token}",)

    finally:
        await bot.session.close()

    await callback.message.edit_text(
        text=text,
        reply_markup=create_manage_bot_keyboard(callback_data),
    )


@NewBotRouter.callback_query(
    MyBotCallbackData.filter(F.action == MyBotAction.create_bot),
)
async def CreateBot(
    callback: CallbackQuery,
    callback_data: MyBotCallbackData,
    state: FSMContext,
):
    await callback.message.delete()

    bot_username = await get_bot_username(callback.bot)

    text = (
        "1️⃣Перейдите к @BotFather. Для этого нажмите на его имя, \n"
        'а потом "Send Message", если это потребуется.\n'
        "2️⃣Создайте нового бота у него. Для этого внутри @BotFather\n"
        'используйте команду "newbot" (сначала вам нужно будет\n'
        "придумать название, оно может быть на русском; потом нужно\n"
        "придумать вашу ссылку, она должна быть на английском и\n"
        'обязательно заканчиваться на "bot", например "NewsBot").\n'
        "3️⃣Скопируйте API токен, который вам выдаст @BotFather\n"
        f"4️⃣Возвращайтесь обратно в @{bot_username} и пришлите скопированный"
        " API токен"
    )

    callback_data.action = MyBotAction.view_bots
    await callback.message.answer(
        text,
        reply_markup=create_back_keyboard(data=callback_data),
    )

    await state.set_state(FSMFillFrom.get_bot_token)


@NewBotRouter.message(StateFilter(FSMFillFrom.get_bot_token))
async def get_product(message: Message, state: FSMContext, bot: Bot):
    if is_bot_token(message.text):
        new_bot = Bot(token=message.text, session=bot.session)
        if not await db.AddBots(message.text, message.from_user.id):
            await message.answer(
                text="Такой бот уже существует!\n Введите другой токен.",
            )
        else:
            try:
                bot_user = await new_bot.get_me()
            except TelegramUnauthorizedError:
                await message.answer(
                    text="Токен введен неправильно. Попробуйте еще раз."
                )
            await new_bot.delete_webhook(drop_pending_updates=True)
            await new_bot.set_webhook(
                main.OTHER_BOTS_URL.format(bot_token=message.text)
            )
            await state.clear()
            await message.answer(
                f"Бот @{bot_user.username} готов к использованию.",
                reply_markup=create_back_keyboard(
                    text="Мои боты",
                    data=MyBotCallbackData(action=MyBotAction.view_bots),
                ),
            )
    else:
        await message.answer(text="Это не токен")


@NewBotRouter.callback_query(
    MyBotCallbackData.filter(F.action == MyBotAction.delete_bot),
)
async def confirm_delete_bot(
    callback: CallbackQuery,
    callback_data: MyBotCallbackData,
):
    bot = get_bot_by_id(callback_data.bot_id)
    try:
        bot_username = f"@{(await bot.get_me()).username}"
    except TelegramUnauthorizedError:
        bot_username = "Токен недействителен!"
    finally:
        bot.session.close()

    await callback.message.edit_text(
        text=f"Вы точно хотите удалить бота:\n{bot_username} ?",
        reply_markup=create_delete_confirm_keyboard(
            data=callback_data,
        ),
    )


@NewBotRouter.callback_query(
    MyBotCallbackData.filter(
        F.action == MyBotAction.delete_confirmed,
    )
)
async def delete_bot(
    callback: CallbackQuery,
    callback_data: MyBotCallbackData,
):
    token = db.get_bot_token_by_id(callback_data.bot_id)
    try:
        bot = get_bot_by_id(callback_data.bot_id)
        bot_username = await bot.get_me()
        await bot.delete_webhook(drop_pending_updates=True)
        text = f"Бот @{bot_username.username} удален"
    except TelegramUnauthorizedError:
        text = "Токен недействителен.\n Бот успешно удален!"
    finally:
        await bot.session.close()

    await db.DeleteBot(token)

    return await callback.message.edit_text(
        text=text,
        reply_markup=create_back_keyboard(
            text="К ботам",
            data=MyBotCallbackData(action=MyBotAction.view_bots),
        ),
    )
