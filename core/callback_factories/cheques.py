from aiogram.filters.callback_data import CallbackData
from enum import Enum


class ChequeType(Enum):
    personal = "personal"
    multi = "multi"


#  Values are shortened to minimize the size of the callback data.
class SubscriptionType(Enum):
    channel = "c"  # channel
    public_group = "p_g"  # public_group
    private_group = "pr_g"  # private_group


#  Values are shortened to minimize the size of the callback data.
class ChequeAction(Enum):
    choose_type = "c_t"  # "choose_type"
    choose_action = "c_a"  # "choose_action"
    view_checks = "v"  # "view"
    view_check = "v_c"  # "view_check"
    get_amount = "g_a"  # "get_amount"
    get_quantity = "g_q"  # "get_quantity"
    confirm = "cnfm"  # "confirm"
    create = "crt"  # "create"
    choose_subscription_type = "a_s"  # "add_subscription"
    get_chat_link = "g_c_l"  # "get_chat_link"
    view_subscriptions = "v_ss"  # "view_subscriptions"
    view_subscription = "v_s"  # "view_subscription"
    delete = "d"  # "delete"
    delete_check_confirmed = "d_c"  # "delete_confirmed"
    delete_subscription = "d_s"  # "delete_subscription"
    delete_subscription_confirmed = "d_s_c"  # "delete_subscription_confirmed"


class ChequeCallbackData(CallbackData, prefix="chk"):  # prefix="check"
    action: ChequeAction | None = ChequeAction.choose_type
    type: ChequeType | None = None
    id: int | None = None
    amount: float | None = None
    quantity: int | None = None
    number: int | None = None
    subscription_type: SubscriptionType | None = None
    chat_id: int | None = None


class CheckSubscribesCallbackData(CallbackData, prefix="chk_sbscrbs"):
    cheque_number: int
