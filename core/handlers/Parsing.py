import os
import json
import requests
from aiogram.types import Message
from aiogram import F
from core.config import config
from aiogram.fsm.context import FSMContext
import database as db
from aiogram import Bot, Router

ParsingRouter = Router()

# Если админ хочет обновить парсинг
@ParsingRouter.message(F.text == 'Обновить парсинг')
async def SendAll(message: Message, state: FSMContext):
    if config.Service == 'All':
        await ParsingSmmPanel()
        await ParsingSmoService()
    elif config.Service == 'SmmPanel':
        await ParsingSmmPanel()
    else:
        await ParsingSmoService()
    await message.answer('Парсинг прошел успешно')


async def ParsingSmmPanel():
    # Запрос к SMMPanel для парсинга
    key_smm = os.getenv('KEYSMMPANEL')
    url = 'https://smmpanel.ru/api/v1'
    data = {
        'key': key_smm,
        'action': 'services'
    }
    response = requests.post(url, data=data)
    testdata = json.loads(response.text)
    JsonLen = len(testdata)
    # Перебираем полученные данные
    for i in range(0, JsonLen):
        category = (testdata[i]['category'])
        NameProduct = (testdata[i]['name'])
        MinOrder = (testdata[i]['min'])
        MaxOrder = (testdata[i]['max'])
        ParsPrice = (testdata[i]['rate'])
        Price = float(ParsPrice) / 1000 * 95
        Price = round(Price, 2)
        ServiceID = (testdata[i]['service'])
        # Исключаем категорию телеграм что бы не получить бан боты
        if 'Telegram' in category:
            pass
        elif 'Телеграм' in category:
            pass
        else:
            # Добавляем все категории и товары в базу данных
            await db.AddCategory(category, 'SmmPanel')
            ParentId = await db.GetIdParentCategory(category, 'SmmPanel', None)
            await db.AddProduct(ParentId, NameProduct, MinOrder, MaxOrder, Price, ServiceID)


async def ParsingSmoService():
    user_id_smo = os.getenv('USERIDSMOSERVICE')
    key_smo = os.getenv('KEYSMOSERVICE')
    url = 'https://smoservice.media/api/'
    data = {
        'user_id': user_id_smo,
        'api_key': key_smo,
        'action': 'services'
    }
    response = requests.post(url, data=data)
    testdata = json.loads(response.text)
    JsonLen = len(testdata['data'])
    for i in range(0, JsonLen):
        NameProduct = (testdata['data'][i]['name'])
        MinOrder = (testdata['data'][i]['min'])
        MaxOrder = (testdata['data'][i]['max'])
        ParsPrice = (testdata['data'][i]['price'])
        ServiceID = (testdata['data'][i]['id'])
        category = (testdata['data'][i]['root_category_name'])
        sub_category = (testdata['data'][i]['category_name'])
        if 'Telegram' in category:
            pass
        elif 'Телеграм' in category:
            pass
        else:
            # Добавляем все категории и товары в базу данных
            await db.AddCategory(category, 'SmoService')
            if sub_category != '':
                IdCategory = await db.GetIdParentCategory(category, 'SmoService', None)
                await db.AddCategory(sub_category, 'SmoService', IdCategory)
                ParentId = await db.GetIdParentCategory(sub_category, 'SmoService', IdCategory)
            else:
                ParentId = await db.GetIdParentCategory(category, 'SmoService', None)
            await db.AddProduct(ParentId, NameProduct, MinOrder, MaxOrder, ParsPrice, ServiceID)
