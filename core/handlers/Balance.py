# Обработка баланса
import os
from aiogram.filters import StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.types import Message, CallbackQuery
from aiogram import F
from core.keyboards import Button
from core.config import config
from http.server import BaseHTTPRequestHandler
import database as db
from urllib.parse import urlencode
import uuid
import requests
import json
import time
import hmac
import hashlib
from aiogram import Bot, Router

# Глобальные переменные для получения и обновления баланса
Sum = 0.0
order_id = ''
user_id = 0

BalanceRouter = Router()

# Создаем FSM
class FSMFillFrom(StatesGroup):
    ReplenishBalance = State()
    GetPay = State()


# Обработка команды
@BalanceRouter.message(Command('mybalance'))
async def MyBalanceKeyboard(message: Message, state: FSMContext):
    # Вызов главное функции
    await MyBalance(message, state)


# Обработка кнопки Мой Баланс
@BalanceRouter.message(F.text == '🏦Мой баланс')
async def MyBalance(message: Message, state: FSMContext):
    # Получаем баланс из бд с помощью id
    balance = await db.GetBalance(message.from_user.id)
    text = f'Ваш баланс: {balance[0]} руб.\n' \
           '💳 Выберите действие ниже:'
    # Используем FSM
    await message.answer(text, reply_markup=Button.BalanceKeyboard)
    await state.set_state(FSMFillFrom.ReplenishBalance)


@BalanceRouter.callback_query(F.data == 'replenish_balance')
async def replenish_balance(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer('💳 Введите сумму пополнения ниже')
    await state.set_state(FSMFillFrom.ReplenishBalance)


# Обработка FSM для пополнения баланса
@BalanceRouter.message(StateFilter(FSMFillFrom.ReplenishBalance))
async def ReplenishBalance(message: Message, state: FSMContext):
    global Sum
    if message.text.isdigit() is True:
        Sum = float(message.text)
        Shopped = str(os.getenv('SHOPID'))
        SecretKey = str(os.getenv('SECRETKEY'))
        global order_id, user_id
        order_id = uuid.uuid4()
        user_id = message.from_user.id
        data = {
            'shop_id': Shopped,
            'amount': Sum,
            'currency': 'RUB',
            'order_id': order_id,
            'test': 1
        }
        sorted_data = sorted(data.items())
        data_string = urlencode(sorted_data)
        sign = hashlib.md5((data_string + SecretKey).encode()).hexdigest()
        PayUrl = f'https://tegro.money/pay/?{data_string}&sign={sign}'
        await message.answer('Выберите способ оплаты', reply_markup=await Button.TegroPay(PayUrl))
        #await message.answer('Проверить оплату', reply_markup=Button.CheckPay)
        #await message.answer('Если хотите отменить нажмите на кнопку в меню⤵️ ', reply_markup=Button.BackMainKeyboard)
    else:
        await state.clear()


async def tegro_success(request):
    param = request.query.get('order_id')
    param2 = request.query.get('status')
    bot = Bot(token=os.getenv('TOKEN'))
    if param2 == 'success':
        print('пришло')
        await db.UpdateBalance(user_id, Sum)
        await bot.send_message(chat_id=user_id, text='оплата прошла успешно', reply_markup=Button.ReplyStartKeyboard)


async def tegro_fail(request):
    bot = Bot(token=os.getenv('TOKEN'))
    await bot.send_message(user_id, 'оплата не прошла', reply_markup=Button.ReplyStartKeyboard)