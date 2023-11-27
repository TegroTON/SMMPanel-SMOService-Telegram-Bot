from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery


class IsChatIsPrivate(BaseFilter):
    async def __call__(self, message: Message | CallbackQuery) -> bool:
        message = message if isinstance(message, Message) else message.message
        return message.chat.type in {"private"}
