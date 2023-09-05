from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram.filters import ChatMemberUpdatedFilter, JOIN_TRANSITION, LEAVE_TRANSITION
from aiogram.types import ChatMemberUpdated
from core.config import config
import database as db
from aiogram.types import Message


# @config.demo_router.my_chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
# async def added_to_group(updated_member: ChatMemberUpdated) -> None:
# Channel = await config.bot.get_chat(updated_member.chat.id)
# print(Channel)
# Link = Channel.invite_link
# await db.AddChanel(updated_member.chat.id)
