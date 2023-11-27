from enum import IntEnum, auto

from .pagination import PaginationCallbackData


class MyOrdersAction(IntEnum):
    VIEW_ORDERS = auto()
    VIEW_ORDER = auto()
    TRY_PAY = auto()
    CANCEL_ORDER = auto()


class MyOrdersCallbackData(
    PaginationCallbackData, prefix="rdr_nf"
):  # prefix="order_info"
    action: MyOrdersAction = MyOrdersAction.VIEW_ORDERS
    order_id: int | None = None
    filter_active: bool = True
    filter_completed: bool = True
    filter_canceled: bool = False
