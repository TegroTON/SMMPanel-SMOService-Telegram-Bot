from aiogram.types import Message
from aiogram.filters.command import Command
from aiogram import F
from core.keyboards import Button, TextUser
from core.config import config
from aiogram import Bot, Router

FAQRouter = Router()


# Обработка команды и кнопки FAQ
@FAQRouter.message(Command('faq'))
async def FAQCommand(message: Message):
    await FAQ(message)


@FAQRouter.message(F.text == '💡FAQ')
async def FAQ(message: Message):
    await message.answer(TextUser.FAQText)
