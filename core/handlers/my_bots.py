import logging

from aiogram import Bot, F, Router, flags
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.filters import StateFilter, or_f
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.enums.chat_action import ChatAction

import database as db
import main
from core.callback_factories.my_bots import MyBotAction, MyBotCallbackData
from core.config import config
from core.keyboards.my_bots import (
    create_delete_confirm_keyboard,
    create_manage_bot_keyboard,
    create_manage_bots_keyboard,
)
from core.keyboards.utils import create_back_keyboard
from core.text_manager import text_manager as tm
from core.utils.bot import (
    get_bot_by_id,
    get_bot_id_by_token,
    get_bot_username,
    is_bot_token,
)

logger = logging.getLogger(__name__)

my_bots_router = Router()


class CreateBotState(StatesGroup):
    get_bot_token = State()


@my_bots_router.callback_query(
    or_f(
        F.data == "my_bots",
        MyBotCallbackData.filter(F.action == MyBotAction.view_bots),
    )
)
@flags.chat_action(
    action=ChatAction.TYPING,
    interval=1,
    initial_sleep=0.5,
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
            bot_data["bot_username"] = bot_info.username
            if bot_data["bot_username"] != bot_info.username:
                db.update_bot_username(
                    bot_id=bot_data["id"],
                    username=bot_info.username,
                )
        except TelegramUnauthorizedError:
            logger.info("Bot %s is unauthorized!", bot_data["bot_username"])
            bot_data["unauthorized"] = True
            continue
        finally:
            await bot.session.close()

        if bot_data["api_key"] == callback.bot.token:
            bot_data["current"] = True

    await callback.message.edit_text(
        text=tm.message.my_bots(),
        reply_markup=create_manage_bots_keyboard(bots_data),
    )


@my_bots_router.callback_query(
    MyBotCallbackData.filter(F.action == MyBotAction.view_bot),
)
async def view_bot_callback_handler(
    callback: CallbackQuery,
    callback_data: MyBotCallbackData,
    state: FSMContext,
):
    bot = get_bot_by_id(callback_data.bot_id)

    try:
        bot_info = await bot.get_me()

        db.update_bot_username(
            bot_id=callback_data.bot_id,
            username=bot_info.username,
        )

        text = tm.message.my_bots_manage_bot().format(
            bot_username=bot_info.username,
            bot_token=bot.token,
        )

    except TelegramUnauthorizedError:
        text = tm.message.my_bots_manage_unauthorized_bot().format(
            bot_token=bot.token
        )
        await state.set_state(CreateBotState.get_bot_token)
        await state.set_data({"bot_id": callback_data.bot_id})

    finally:
        await bot.session.close()

    await callback.message.edit_text(
        text=text,
        reply_markup=create_manage_bot_keyboard(callback_data),
    )


@my_bots_router.callback_query(
    MyBotCallbackData.filter(F.action == MyBotAction.create_bot),
)
async def create_bot_callback_handler(
    callback: CallbackQuery,
    callback_data: MyBotCallbackData,
    state: FSMContext,
):
    bot_username = await get_bot_username(callback.bot)

    callback_data.action = MyBotAction.view_bots
    await callback.message.edit_text(
        text=tm.message.my_bots_create_instruction().format(
            bot_username=bot_username
        ),
        reply_markup=create_back_keyboard(data=callback_data),
    )

    await state.set_state(CreateBotState.get_bot_token)


@my_bots_router.message(StateFilter(CreateBotState.get_bot_token))
async def get_token_handler(
    message: Message,
    state: FSMContext,
    bot: Bot,
):
    state_data = await state.get_data()

    token = message.text

    if not is_bot_token(token):
        await message.answer(
            text=tm.message.my_bots_not_token(),
        )
        return

    new_bot = Bot(token=message.text, session=AiohttpSession())

    if get_bot_id_by_token(token) or token == config.BOT_TOKEN:
        await message.answer(
            text=tm.message.my_bots_already_exist(),
        )
        return

    try:
        new_bot_info = await new_bot.get_me()
    except TelegramUnauthorizedError:
        await message.answer(
            text=tm.message.my_bots_token_incorrect(),
        )
        return

    if "bot_id" in state_data:
        db.update_bot(state_data["bot_id"], token)
        await message.answer(
            text=tm.message.my_bots_manage_bot().format(
                bot_username=new_bot_info.username,
                bot_token=token,
            ),
            reply_markup=create_manage_bot_keyboard(
                MyBotCallbackData(
                    action=MyBotAction.view_bot,
                    bot_id=state_data["bot_id"],
                ),
            ),
        )
        return
    else:
        db.add_bot(
            api_token=message.text,
            id_user=message.from_user.id,
            bot_username=new_bot_info.username,
        )

    await new_bot.delete_webhook(drop_pending_updates=True)
    await new_bot.set_webhook(
        main.OTHER_BOTS_URL.format(bot_token=message.text)
    )

    await new_bot.session.close()

    await state.set_state(None)

    await message.answer(
        text=tm.message.my_bots_bot_ready().format(
            bot_username=new_bot_info.username
        ),
        reply_markup=create_back_keyboard(
            text=tm.button.my_bots(),
            data=MyBotCallbackData(action=MyBotAction.view_bots),
        ),
    )


@my_bots_router.callback_query(
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
        bot_username = tm.message.my_bots_token_is_retired()
    finally:
        await bot.session.close()

    await callback.message.edit_text(
        text=tm.message.my_bots_delete_confirm().format(
            bot_username=bot_username
        ),
        reply_markup=create_delete_confirm_keyboard(
            data=callback_data,
        ),
    )


@my_bots_router.callback_query(
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
        bot_username = (await bot.get_me()).username
        await bot.delete_webhook(drop_pending_updates=True)
    except TelegramUnauthorizedError:
        bot_username = tm.message.my_bots_token_is_retired()
    finally:
        await bot.session.close()

    db.delete_bot(token)

    return await callback.message.edit_text(
        text=tm.message.my_bots_delete_confirmed().format(
            bot_username=bot_username,
        ),
        reply_markup=create_back_keyboard(
            text=tm.button.my_bots(),
            data=MyBotCallbackData(action=MyBotAction.view_bots).pack(),
        ),
    )
