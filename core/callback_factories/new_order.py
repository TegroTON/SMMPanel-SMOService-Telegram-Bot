from enum import IntEnum

from .pagination import PaginationCallbackData


class NewOrderAction(IntEnum):
    CHOOSE_CATEGORY = 1
    CHOOSE_SUBCATEGORY = 2
    CHOOSE_PRODUCT = 3
    ENTER_QUANTITY = 4
    ENTER_LINK = 5


class NewOrderCallbackData(
    PaginationCallbackData, prefix="nw_rdr"
):  # prefix: new_order
    action: NewOrderAction | None = None
    category_id: int | None = None
    subcategory_id: int | None = None
    product_id: int | None = None
    quantity: float | None = None
    url: str | None = None
