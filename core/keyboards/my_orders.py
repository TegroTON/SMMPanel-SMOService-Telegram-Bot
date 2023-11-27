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
from core.text_manager import text_manager as tm

from .utils import create_pagination_buttons, create_to_main_menu_button


def create_orders_list_keyboard(
    data: MyOrdersCallbackData,
    orders: List[Dict[str, Any]],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    filters = {
        "active": data.filter_active,
        "completed": data.filter_completed,
        "canceled": data.filter_canceled,
    }

    is_any_off = not all(filters.values())

    builder.row(
        InlineKeyboardButton(
            text=f"🟢 [{'✔️' if filters['active'] else ' '}]",
            callback_data=data.model_copy(
                update={
                    "filter_active": not filters["active"],
                }
            ).pack(),
        ),
        InlineKeyboardButton(
            text=f"✅ [{'✔️' if filters['completed'] else ' '}]",
            callback_data=data.model_copy(
                update={
                    "filter_completed": not filters["completed"],
                }
            ).pack(),
        ),
        InlineKeyboardButton(
            text=f"❌ [{'✔️' if filters['canceled'] else ' '}]",
            callback_data=data.model_copy(
                update={
                    "filter_canceled": not filters["canceled"],
                }
            ).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=f"🛒 Все заказы[{'✔️' if not is_any_off else ' '}]",
            callback_data=MyOrdersCallbackData(filter_canceled=True).pack()
            if is_any_off
            else "not_handled_callback",
        ),
    )

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
            text=tm.button.new_order(),
            callback_data="new_order",
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=tm.button.back(),
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
            InlineKeyboardButton(
                text=tm.button.pay(),
                callback_data=data.model_copy(
                    update={"action": MyOrdersAction.TRY_PAY}
                ).pack(),
            )
        )

    builder.row(
        InlineKeyboardButton(
            text=tm.button.my_orders(),
            callback_data=data.model_copy(
                update={"action": MyOrdersAction.VIEW_ORDERS}
            ).pack(),
        )
    )

    builder.row(
        create_to_main_menu_button(),
    )

    return builder.as_markup()


def create_replenish_for_order_keyboard(
    data: MyOrdersCallbackData,
    amount: float,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=tm.button.pay_amount().format(amount=amount),
            callback_data=WalletCallbackData(
                action=WalletAction.get_amount,
                amount=amount,
            ).pack(),
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=tm.button.replenish_balance(),
            callback_data=WalletCallbackData(
                action=WalletAction.replenish,
            ).pack(),
        )
    )

    data.action = MyOrdersAction.VIEW_ORDER
    builder.row(
        InlineKeyboardButton(
            text=tm.button.order(),
            callback_data=data.pack(),
        )
    )

    return builder.as_markup()
