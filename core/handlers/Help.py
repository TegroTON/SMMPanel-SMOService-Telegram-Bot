from aiogram.types import Message
from aiogram.filters.command import Command
from aiogram import F
from core.keyboards import TextUser
from core.config import config
from aiogram import Bot, Router
from core.handlers import FAQ

HelpRouter = Router()


# Обработка команды и кнопки Help
@HelpRouter.message(Command('help'))
async def HelpCommand(message: Message):
    await FAQ.FAQ(message)


@HelpRouter.message(F.text == '⛑️Помощь')
async def Help(message: Message):
    await message.answer(TextUser.HelpMessage)
