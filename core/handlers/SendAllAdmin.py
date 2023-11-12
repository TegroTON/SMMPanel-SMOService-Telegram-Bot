from aiogram import F, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import database as db
from core.config import config
from core.keyboards import Button

SendAllRouter = Router()


# Создаем FSM
class FSMFillFrom(StatesGroup):
    CheckTextSendAll = State()


# Обработка команды рассылки
@SendAllRouter.message(F.text == "Рассылка")
async def SendAll(message: Message, state: FSMContext):
    if message.from_user.id == config.ADMIN_ID:
        await message.answer(
            text=(
                "<b>Введите текст рассылки</b>\n"
                "Рассылка будет произведена от текущего бота."
            ),
            reply_markup=Button.BackMainKeyboard,
            parse_mode=ParseMode.HTML,
        )
        await state.set_state(FSMFillFrom.CheckTextSendAll)


# Обработка FSM
@SendAllRouter.message(StateFilter(FSMFillFrom.CheckTextSendAll))
async def CheckSendAll(message: Message, state: FSMContext):
    users = await db.GetUsers()

    for user in users:
        try:
            await message.bot.send_message(
                user[0], message.text, parse_mode=ParseMode.HTML
            )
        # Если не получилось значит пользователь нас заблокировал
        except TelegramAPIError:
            await message.answer(f"Пользователь {user[0]} заблокировал бот")

    await message.answer("Рассылка прошла успешно")
    await state.clear()
