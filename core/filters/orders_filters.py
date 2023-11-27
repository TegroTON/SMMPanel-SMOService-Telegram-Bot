from typing import Dict

import validators
from aiogram.filters import BaseFilter
from aiogram.types import Message


class IsFilterUserId(BaseFilter):
    async def __call__(self, message: Message) -> bool | Dict[str, int]:
        if message.text.startswith("id-") and message.text[3:].isdigit():
            return {"user_id": int(message.text[3:])}

        return False


class IsFilterUrl(BaseFilter):
    async def __call__(self, message: Message) -> bool | Dict[str, str]:
        if (
            message.text.startswith("link-")
            and validators.domain(message.text[5:])
            or validators.url(message.text[5:])
        ):
            return {"link": message.text[5:]}

        return False


class IsFilterOrderId(BaseFilter):
    async def __call__(self, message: Message) -> bool | Dict[str, int]:
        if message.text.startswith("o_id-") and message.text[5:].isdigit():
            return {"order_id": int(message.text[5:])}

        return False
