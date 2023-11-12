from typing import Any, Dict, List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.callback_factories.my_orders import (
    MyOrdersAction,
    MyOrdersCallbackData,
)
from core.callback_factories.wallet import WalletAction, WalletCallbackData
from core.config import config
from core.service_provider.order_status import OrderStatus

from .main_menu import to_main_menu_button
from .utils import create_pagination_buttons


def create_orders_list_keyboard(
    data: MyOrdersCallbackData,
    orders: List[Dict[str, Any]],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    has_next_page = False
    if len(orders) > config.PAGINATION_CATEGORIES_PER_PAGE:
        orders = orders[: config.PAGINATION_CATEGORIES_PER_PAGE]
        has_next_page = True

    data.action = MyOrdersAction.VIEW_ORDER
    for order in orders:
        builder.row(
            InlineKeyboardButton(
                text="{order_id}{status}{name}".format(
                    order_id=f'{order["id"]:>{5}}',
                    status=f'{OrderStatus(order["status"]).icon:>{1}}',
                    name=f'{order["name"]: >{45}}',
                ),
                callback_data=data.model_copy(
                    update={
                        "order_id": order["id"],
                    }
                ).pack(),
            )
        )

    data.action = MyOrdersAction.VIEW_ORDERS
    pagination_buttons = create_pagination_buttons(data, has_next_page)

    builder.row(*pagination_buttons)

    builder.row(
        InlineKeyboardButton(
            text="Создать новый заказ",
            callback_data="new_order",
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data="wallet",
        )
    )

    return builder.as_markup(resize_keyboard=True)


def create_order_info_keyboard(
    data: MyOrdersCallbackData,
    with_pay_button: bool = False,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if with_pay_button:
        builder.row(
            # InlineKeyboardButton(
            #     text="Отменить",
            #     callback_data=data.model_copy(
            #         update={"action": MyOrdersAction.CANCEL_ORDER}
            #     ).pack(),
            # ),
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


def create_replenish_for_order_keyboard(
    data: MyOrdersCallbackData,
    amount: float,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=f"Пополнить на {amount} руб.",
            callback_data=WalletCallbackData(
                action=WalletAction.get_amount,
                amount=amount,
            ).pack(),
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="Пополнить баланс",
            callback_data=WalletCallbackData(
                action=WalletAction.replenish,
            ).pack(),
        )
    )

    data.action = MyOrdersAction.VIEW_ORDER
    builder.row(
        InlineKeyboardButton(
            text="К заказу",
            callback_data=data.pack(),
        )
    )

    return builder.as_markup()
