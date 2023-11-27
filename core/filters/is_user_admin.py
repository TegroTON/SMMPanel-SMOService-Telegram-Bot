from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from core.config import config


class IsUserAdmin(BaseFilter):
    async def __call__(self, message: Message | CallbackQuery) -> bool:
        return message.from_user.id == config.ADMIN_ID
