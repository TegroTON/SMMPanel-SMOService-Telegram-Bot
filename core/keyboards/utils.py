from typing import List

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.callback_factories.pagination import PaginationCallbackData
from core.config import config
from core.service_provider.order_status import OrderStatus
from core.text_manager import text_manager as tm


def create_back_keyboard(
    data: CallbackData | str,
    text: str | None = None,
) -> InlineKeyboardMarkup:
    if not text:
        text = tm.button.back()

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=text,
            callback_data=data.pack()
            if isinstance(data, CallbackData)
            else data,
        )
    )

    return builder.as_markup()


def create_pagination_buttons(
    data: PaginationCallbackData,
    has_next_page: bool = False,
) -> List[InlineKeyboardButton]:
    page = data.page

    buttons = []

    if page > 1:
        buttons.append(
            InlineKeyboardButton(
                text=tm.button.pagination_prev(),
                callback_data=data.model_copy(
                    update={"page": page - 1}
                ).pack(),
            )
        )

    if has_next_page:
        buttons.append(
            InlineKeyboardButton(
                text=tm.button.pagination_next(),
                callback_data=data.model_copy(
                    update={"page": page + 1},
                ).pack(),
            )
        )

    return buttons


def create_orders_buttons(
    data: PaginationCallbackData,
    orders: List[dict],
) -> List[InlineKeyboardButton]:
    buttons = []
    for order in orders:
        buttons.append(
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

    return buttons


def create_to_referrals_button() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=tm.button.referrals(),
        callback_data="earn",
    )


def create_to_cheques_button() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=tm.button.cheques(),
        callback_data="cheque",
    )


def create_to_new_order_button() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=tm.button.new_order(),
        callback_data="new_order",
    )


def create_to_main_menu_button() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=tm.button.main_menu(),
        callback_data="main_menu",
    )


def create_to_admin_panel_button() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=tm.button.admin_panel(),
        callback_data="admin_panel",
    )


def create_to_wallet_button() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=tm.button.wallet(),
        callback_data="wallet",
    )


def create_to_my_bots_button() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=tm.button.my_bots(),
        callback_data="my_bots",
    )


def create_to_wallet_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                create_to_wallet_button(),
            ],
        ],
    )


def create_to_faq_button() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=tm.button.faq(),
        web_app=WebAppInfo(url=config.FAQ_URL),
    )


def create_to_help_button() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=tm.button.help(),
        web_app=WebAppInfo(url=config.HELP_URL),
    )


def create_confirm_keyboard(
    accept_text: str,
    accept_data: CallbackData,
    decline_text: str,
    decline_data: CallbackData,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=accept_text,
            callback_data=accept_data.pack(),
        ),
        InlineKeyboardButton(
            text=decline_text,
            callback_data=decline_data.pack(),
        ),
    )

    return builder.as_markup()
