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
import hashlib
import uuid
from aiogram import Bot, Router

AdminGetServiceRouter = Router()


@AdminGetServiceRouter.message(F.text == 'Выбрать сервис для создания заказа')
async def CreateAnOrder(message: Message):
    await message.answer('Выберите сервис с которого буду браться продукты и делаться заказы(значение по умолчанию Вместе)',
                         reply_markup=Button.GetServiceKeyboard)
    print(config.Service)


@AdminGetServiceRouter.callback_query(F.data == 'SmoService')
async def CheckPay(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    config.Service = 'SmoService'
    await callback.message.answer('Теперь сервис для обработки заказов SmoService')

@AdminGetServiceRouter.callback_query(F.data == 'SmmPanelService')
async def CheckPay(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    config.Service = 'SmmPanel'
    await callback.message.answer('Теперь сервис для обработки заказов SmmPanel')


@AdminGetServiceRouter.callback_query(F.data == 'All_service')
async def CheckPay(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    config.Service = 'All'
    await callback.message.answer('Теперь работает сразу два сервиса для обработки заказов')