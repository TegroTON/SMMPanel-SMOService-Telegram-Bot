# Создание заказа
import os
from aiogram import F
from urllib.parse import urlencode
from aiogram.filters import StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.types import Message, CallbackQuery
from core.keyboards import Button
from core.config import config
import database as db
import validators
import requests
import json
import time
import hmac
from core.handlers import Balance
import hashlib
import uuid
from aiogram import Bot, Router

# Глобальные переменные для заказа
ProductId = 0
PriceProduct = 0
Quantity = 0.0
sum = 0.0
order_id = ''
Service = ''

OrderRouter = Router()


# Создаем FSM
class FSMFillFrom(StatesGroup):
    get_product = State()
    get_url = State()


# Обработка команды
@OrderRouter.message(Command('neworder'))
async def CreateAnOrderKeyboard(message: Message):
    # Вызов функции создать заказ
    await CreateAnOrder(message)


# Обработка нажатие кнопки создать заказ
@OrderRouter.message(F.text == '🔥Создать новый заказ')
async def CreateAnOrder(message: Message):
    # Просим выбрать категорию для товара
    await message.answer('Выберите категорию, в которой вы бы хотели заказать услугу:',
                         reply_markup=await Button.CategoryMarkup('buy'))


# После выбора категории обрабатываем выбранную строку
@OrderRouter.callback_query(F.data.startswith("buy_category"))
async def NameCategory(callback: CallbackQuery):
    global Service
    # Получаем id категории товара
    ParentId = int(callback.data[13:])
    # Вывод все товара у кого id категории равен этой
    Service = await db.GetServiceCategory(ParentId)
    print(Service)
    SubCategroy = await db.GetSubCategory(ParentId)
    if SubCategroy is None:
        await callback.message.answer('Выберите товар', reply_markup=await Button.CheckProduct('buy', ParentId))
    else:
        await callback.message.answer('Выберите подкатегорию', reply_markup=await Button.SubCategory('buy', ParentId))
    await callback.message.delete()


@OrderRouter.callback_query(F.data.startswith("buy_subcategory"))
async def buy_subcategory(callback: CallbackQuery):
    global Service
    ParentId = int(callback.data[16:])
    Service = await db.GetServiceCategory(ParentId)
    print(Service)
    await callback.message.answer('Выберите товар', reply_markup=await Button.CheckProduct('buy', ParentId))
    await callback.message.delete()


# Обработка выбранного товара
@OrderRouter.callback_query(F.data.startswith('buy_product'))
async def buy_product(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    global ProductId
    global PriceProduct
    global Quantity
    # Получаем id товара из бд
    ProductId = int(callback.data[12:])
    InfoProduct = await db.GetOneProduct(ProductId)
    PriceProduct = InfoProduct[5]
    Quantity = InfoProduct[3]
    # Выводим данные о товаре
    text = f'👴Заказ услуги "{InfoProduct[2]}"\n' \
           f'💳 Цена - {InfoProduct[5]}. За одну единицу (Подписчик, лайк, репост)' \
           f'👇 Введите количество для заказа от {InfoProduct[3]} до {InfoProduct[4]}'
    await callback.message.answer(text, reply_markup=Button.BackMainKeyboard)
    await state.set_state(FSMFillFrom.get_url)


# Обработка кнопки назад
@OrderRouter.message(F.text == 'Назад')
async def CheckPay(message: Message, state: FSMContext):
    # Останавливаем FSM
    await state.clear()
    await message.delete()
    # Проверяем является ли пользователь админом
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        await message.answer('Вы попали в админ-панель', reply_markup=Button.ReplyAdminMainKeyboard)
    else:
        await message.answer('Выберите в меню ниже интересующий Ваc раздел:', reply_markup=Button.ReplyStartKeyboard)


# Используем машину состояний для обработки количества товара
@OrderRouter.message(StateFilter(FSMFillFrom.get_url))
async def get_product(message: Message, state: FSMContext):
    global Quantity
    # Проверяем является ли отправленное значение числом
    if message.text.isdigit() is True:
        # Передаем кол во товара в глобальную переменную
        if int(message.text) < Quantity:
            await message.answer('Введите число в указанном диапазоне')
        else:
            Quantity = float(message.text)
            await state.set_state(FSMFillFrom.get_product)
            await message.answer('Введите адрес целевой страницы:', reply_markup=Button.BackMainKeyboard)
    else:
        await message.answer('Введите число !!!!!')


# Оформляем заказа в SMMPanel
@OrderRouter.message(StateFilter(FSMFillFrom.get_product))
async def get_product(message: Message, state: FSMContext):
    # Проверяем является ли то что отправил пользователь ссылкой
    if validators.url(message.text) is True:
        # Создаем запрос на SMMPanel для создания нового заказа
        UserId = message.from_user.id
        ServiceId = await db.GetProductServiceId(ProductId)
        balance = await db.GetBalance(message.from_user.id)
        Sum = Quantity * PriceProduct
        # Если сумма заказа больше чем баланс пользователя
        if float(Sum) > float(balance[0]):
            # Создаем ссылку для оплаты Tegro
            global order_id, sum
            sum = Sum
            order_id = uuid.uuid4()
            data = {
                'shop_id': str(os.getenv('SHOPID')),
                'amount': Sum,
                'currency': 'RUB',
                'order_id': order_id,
                'test': 1
            }
            sorted_data = sorted(data.items())
            data_string = urlencode(sorted_data)
            sign = hashlib.md5((data_string + str(os.getenv('SECRETKEY'))).encode()).hexdigest()
            PayUrl = f'https://tegro.money/pay/?{data_string}&sign={sign}'
            await message.answer(f'Недостаточно средств на балансе. Пополните баланс ниже на {sum}')
            await Balance.MyBalance(message, state)
        else:
            # Если денег хватает, то отправляем заказ в SMMPanel
            await db.WriteOffTheBalance(UserId, Sum)
            Referrals = await db.GetReferral(UserId)
            if Referrals is not None:
                SecondLevelReferral = await db.GetReferral(Referrals)
                if SecondLevelReferral is not None:
                    ReferralSum = Sum * 0.04
                    await db.UpdateMoneyReferral(SecondLevelReferral, ReferralSum)
                    await db.UpdateBalance(SecondLevelReferral, ReferralSum)
                ReferralSum = Sum * 0.12
                await db.UpdateMoneyReferral(Referrals, ReferralSum)
                await db.UpdateBalance(Referrals, ReferralSum)
            Url = message.text
            if Service == 'SmmPanel':
                res = await OrderSmmPanel(Url, ServiceId, UserId, Sum)
                await message.answer(res)
            elif Service == 'SmoService':
                res = await OrderSmoService(Url, ServiceId, UserId, Sum)
                await message.answer(res)
        await state.clear()
    # Если пользователь отправил не ссылку
    else:
        await message.answer('Произошла ошибка. Описание:\n'
                             'URL введен неверно\n'
                             '\n'
                             'Попробуйте создать заказ заново\n')



async def OrderSmmPanel(Url, ServiceId, UserId, Sum):
    key_smm = os.getenv('KEYSMMPANEL')
    url = 'https://smmpanel.ru/api/v1'
    data = {
        'key': key_smm,
        'action': 'add',
        'service': ServiceId,
        'link': Url,
        'quantity': Quantity
    }
    response = requests.post(url, data=data)
    OrderData = json.loads(response.text)
    Status = (OrderData['status'])
    Order_Id = (OrderData['order'])
    # Добавляем в бд все данные о заказе
    res = await db.AddOrders(UserId, ProductId, Quantity, Sum, ServiceId[0], Url, Order_Id, Status)
    text = f'Заказ номер {Order_Id} получен.\n' \
           f'Статус заказа в обработке'
    return text


async def OrderSmoService(Url, ServiceId, UserId, Sum):
    user_id_smo = os.getenv('USERIDSMOSERVICE')
    key_smo = os.getenv('KEYSMOSERVICE')
    url = 'https://smoservice.media/api/'
    data = {
        'user_id': user_id_smo,
        'api_key': key_smo,
        'action': 'create_order',
        'service_id': ServiceId[0],
        'count': Quantity,
        'url': Url,
    }
    response = requests.post(url, data=data)
    OrderData = json.loads(response.text)
    Status = (OrderData['type'])
    Order_Id = (OrderData['data']['order_id'])
    # Добавляем в бд все данные о заказе
    res = await db.AddOrders(UserId, ProductId, Quantity, Sum, ServiceId[0], Url, Order_Id, Status)
    text = f'Заказ номер {Order_Id} получен.\n' \
           f'Статус заказа в обработке'
    return text
