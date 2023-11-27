from aiogram.filters.callback_data import CallbackData
from enum import Enum


class MyBotAction(Enum):
    view_bots = "vw_bts"
    view_bot = "vw_bt"
    create_bot = "crt_bt"
    change_token = "chng_tk"
    delete_bot = "del_bt"
    delete_confirmed = "dlt_cnfrmd"


class MyBotCallbackData(CallbackData, prefix="m_bt"):  # prefix="my_bot"
    action: MyBotAction = MyBotAction.view_bots
    bot_id: int | None = None
