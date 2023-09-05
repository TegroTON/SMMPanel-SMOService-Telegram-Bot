import os
from aiogram.types import Message
from aiogram import F
from core.config import config
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from aiogram.filters import StateFilter
import database as db
from aiogram.enums.parse_mode import ParseMode
from core.keyboards import Button
from aiogram import Bot, Router

SendAllRouter = Router()

# Создаем FSM
class FSMFillFrom(StatesGroup):
    CheckTextSendAll = State()


# Обработка команды рассылки
@SendAllRouter.message(F.text == 'Рассылка')
async def SendAll(message: Message, state: FSMContext):
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        await message.answer(f'<b>Введите текст рассылки</b>', parse_mode=ParseMode.HTML, reply_markup=Button.BackMainKeyboard)
        await state.set_state(FSMFillFrom.CheckTextSendAll)


# Обработка FSM
@SendAllRouter.message(StateFilter(FSMFillFrom.CheckTextSendAll))
async def CheckSendAll(message: Message, state: FSMContext):
    # Получем из бд всех юзеров бота
    users = await db.GetUsers()
    # Перебираем и отправляем сообщение
    for user in users:
        try:
            await config.bot.send_message(user[0], message.text, parse_mode=ParseMode.HTML)
        # Если не получилось значит пользователь нас заблокировал
        except:
            await message.answer(f'Пользователь {user[0]} заблокировал бот')
    await message.answer('Рассылка прошла успешно')
    await state.clear()
