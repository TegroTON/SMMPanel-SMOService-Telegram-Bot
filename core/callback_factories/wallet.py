from aiogram.filters.callback_data import CallbackData
from enum import Enum


#  Values are shortened to minimize the size of the callback data.
class WalletAction(Enum):
    choose_action = "c_a"
    replenish = "rplnsh"
    get_amount = "g_a"
    check_paylink_status = "c_p_s"
    history = "hstr"
    history_document = "hstr_d"


class WalletCallbackData(CallbackData, prefix="wllt"):  # prefix="wallet"
    action: WalletAction | None = None
    amount: float | None = None
    order_id: str | None = None
