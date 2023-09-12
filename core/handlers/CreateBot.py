from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from core.config import config
from os import getenv
from typing import Any, Dict, Union
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery
import main
from core.keyboards import Button
from aiogram.filters import StateFilter
from aiogram.utils.token import TokenValidationError, validate_token
from aiogram.exceptions import TelegramUnauthorizedError
import database as db

NewBotRouter = Router()


class FSMFillFrom(StatesGroup):
    get_bot_token = State()


def is_bot_token(value: str) -> Union[bool, Dict[str, Any]]:
    try:
        validate_token(value)
    except TokenValidationError:
        return False
    return True


@NewBotRouter.message(F.text == '🤖Мои Боты')
async def command_add_bot(message: Message, state: FSMContext, bot: Bot) -> Any:
    await state.clear()
    Text = '1️⃣Перейдите к @BotFather. Для этого нажмите на его имя, \n' \
           'а потом "Send Message", если это потребуется.\n' \
           '2️⃣Создайте нового бота у него. Для этого внутри @BotFather\n' \
           'используйте команду "newbot" (сначала вам нужно будет\n' \
           'придумать название, оно может быть на русском; потом нужно\n' \
           'придумать вашу ссылку, она должна быть на английском и\n' \
           'обязательно заканчиваться на "bot", например "NewsBot").\n' \
           '3️⃣Скопируйте API токен, который вам выдаст @BotFather\n' \
           '4️⃣Возвращайтесь обратно в @SmmTegroTest_Bot и пришлите скопированный API токен'
    await message.answer(Text, reply_markup=Button.BotsKeyboard)


@NewBotRouter.callback_query(F.data == 'CreateBot')
async def CreateBot(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await callback.message.delete()
    TextCreate = '1️⃣Перейдите к @BotFather. Для этого нажмите на его имя, \n' \
                 'а потом "Send Message", если это потребуется.\n' \
                 '2️⃣Создайте нового бота у него. Для этого внутри @BotFather\n' \
                 'используйте команду "newbot" (сначала вам нужно будет\n' \
                 'придумать название, оно может быть на русском; потом нужно\n' \
                 'придумать вашу ссылку, она должна быть на английском и\n' \
                 'обязательно заканчиваться на "bot", например "NewsBot").\n' \
                 '3️⃣Скопируйте API токен, который вам выдаст @BotFather\n' \
                 '4️⃣Возвращайтесь обратно в @SmmTegroTest_Bot и пришлите скопированный API токен'
    await callback.message.answer(TextCreate)
    await state.set_state(FSMFillFrom.get_bot_token)


@NewBotRouter.message(StateFilter(FSMFillFrom.get_bot_token))
async def get_product(message: Message, state: FSMContext, bot: Bot):
    if is_bot_token(message.text):
        new_bot = Bot(token=message.text, session=bot.session)
        if not await db.AddBots(message.text, message.from_user.id):
            await message.answer('Такой бот уже существует', reply_markup=Button.ReplyStartKeyboard)
        else:
            try:
                bot_user = await new_bot.get_me()
            except TelegramUnauthorizedError:
                await message.answer("Токен введен неправильно. Попробуйте еще раз", reply_markup=Button.ReplyStartKeyboard)
            await new_bot.delete_webhook(drop_pending_updates=True)
            await new_bot.set_webhook(main.OTHER_BOTS_URL.format(bot_token=message.text))
            await state.clear()
            await message.answer(f"Бот @{bot_user.username} готов к использованию", reply_markup=Button.ReplyStartKeyboard)
    else:
        await message.answer('Это не токен', reply_markup=Button.ReplyStartKeyboard)


@NewBotRouter.callback_query(F.data.startswith('delete_bot_'))
async def delete_bot(call: CallbackQuery, bot: Bot):
    DeleteBotApi = str(call.data[11:])
    await db.DeleteBot(DeleteBotApi)
    await call.message.delete()
    new_bot = Bot(token=DeleteBotApi, session=bot.session)
    try:
        bot_user = await new_bot.get_me()
    except TelegramUnauthorizedError:
        return call.message.answer("Токен введен неправильно. Попробуйте еще раз")
    await new_bot.delete_webhook(drop_pending_updates=True)
    return await call.message.answer(f"Бот @{bot_user.username} удален")


@NewBotRouter.callback_query(F.data == 'DeleteBot')
async def DeleteBot(call: CallbackQuery, bot: Bot, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Нажмите на API токен бота которого удалить", reply_markup=await Button.DeleteBot(call.from_user.id))

