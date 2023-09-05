import os
from aiogram.types import Message
from core.keyboards import Button
from core.config import config
from aiogram import F
from aiogram import Bot, Router

AdminRouter = Router()


# Обрабатываем нажатие на кнопку Админ-Панель
@AdminRouter.message(F.text == 'Админ-панель')
async def CreateAnOrder(message: Message):
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        await message.answer('Выберите действие', reply_markup=Button.ReplyAdminPanelKeyboard)
    else:
        await message.answer('Я не знаю такой команды')

