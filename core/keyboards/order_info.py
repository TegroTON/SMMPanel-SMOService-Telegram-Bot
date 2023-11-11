from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.callback_factories.my_orders import (
    MyOrdersAction,
    MyOrdersCallbackData,
)

from .main_menu import to_main_menu_button


def create_order_info_keyboard(
    data: MyOrdersCallbackData,
    status: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if status == "pending":
        builder.row(
            InlineKeyboardButton(
                text="Оплатить",
                callback_data=data.model_copy(
                    update={"action": MyOrdersAction.TRY_PAY}
                ).pack(),
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="К заказам",
            callback_data=data.model_copy(
                update={"action": MyOrdersAction.VIEW_ORDERS}
            ).pack(),
        )
    )

    builder.row(
        to_main_menu_button,
    )

    return builder.as_markup()
