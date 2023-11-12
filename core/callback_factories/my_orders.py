from enum import IntEnum

from .pagination import PaginationCallbackData


class MyOrdersAction(IntEnum):
    VIEW_ORDERS = 1
    VIEW_ORDER = 2
    TRY_PAY = 3
    CANCEL_ORDER = 4


class MyOrdersCallbackData(
    PaginationCallbackData, prefix="rdr_nf"
):  # prefix="order_info"
    action: MyOrdersAction
    order_id: int | None = None
