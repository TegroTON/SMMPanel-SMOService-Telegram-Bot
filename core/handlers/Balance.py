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
import datetime
import jinja2
from aiogram import Bot, Router
from aiogram.types.input_file import FSInputFile

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
@BalanceRouter.message(F.text == '👛 Кошелёк')
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
    else:
        await state.clear()


@BalanceRouter.callback_query(F.data == 'history_balance')
async def history_balance(callback: CallbackQuery, state: FSMContext):
    Datas = await db.Get_History(callback.from_user.id)
    TextAnswer = ''
    date = ''
    Id = 0
    if Datas:
        for data in Datas:
            if data[0] > Id:
                Id = data[0]
                date = data[4]
                month = data[4].split('-')
                TextAnswer = f'<b>• {month[2]}.{month[1]}.{month[0]}</b>\n'
        for data in Datas:
            if data[4] == date:
                Time = data[5].split(':')
                if data[2] > 0:
                    TextAnswer += f'<i>{Time[0]}:{Time[1]} {data[3]} +{data[2]} рублей</i>\n'
                else:
                    TextAnswer += f'<i>{Time[0]}:{Time[1]} {data[3]} {data[2]} рублей</i>\n'
        await callback.message.answer(TextAnswer, reply_markup=Button.GetAllHistoryKeyboard)
        await callback.message.delete()
    else:
        TextAnswer = 'У вас нет операций по счету'
        await callback.answer(TextAnswer)


@BalanceRouter.callback_query(F.data == 'Get_All_History')
async def Get_All_History(callback: CallbackQuery, state: FSMContext, bot: Bot):
    Datas = await db.Get_History(callback.from_user.id)
    file = open(f"отчет_{callback.from_user.id}.txt", "w+")
    date = ''
    for data in Datas:
        if date != data[4]:
            date = data[4]
            day = date.split('-')[2]
            month = date.split('-')[1]
            year = date.split('-')[0]
            file.write(f"{day}.{month}.{year}\n")
        hour = data[5].split(':')[0]
        minute = data[5].split(':')[1]
        file.write(f"{hour}:{minute} {data[3]} {data[2]} рублей\n")
    file.close()
    document = FSInputFile(f'отчет_{callback.from_user.id}.txt')
    await bot.send_document(callback.from_user.id, document)
    await callback.message.delete()

async def tegro_success(request):
    param = request.query.get('order_id')
    param2 = request.query.get('status')
    bot = Bot(token=os.getenv('TOKEN'))
    if param2 == 'success':
        await db.UpdateBalance(user_id, Sum)
        await bot.send_message(chat_id=user_id, text='оплата прошла успешно', reply_markup=Button.ReplyStartKeyboard)
        await db.Add_History(user_id, Sum, 'Пополнение')


async def tegro_fail(request):
    bot = Bot(token=os.getenv('TOKEN'))
    await bot.send_message(user_id, 'оплата не прошла', reply_markup=Button.ReplyStartKeyboard)