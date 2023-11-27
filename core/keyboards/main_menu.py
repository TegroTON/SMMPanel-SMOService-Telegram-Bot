from aiogram.types import (
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.text_manager import text_manager as tm

from .utils import (
    create_to_admin_panel_button,
    create_to_cheques_button,
    create_to_faq_button,
    create_to_help_button,
    create_to_main_menu_button,
    create_to_my_bots_button,
    create_to_new_order_button,
    create_to_referrals_button,
    create_to_wallet_button,
)


def get_main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        create_to_new_order_button(),
    )

    builder.row(
        create_to_wallet_button(),
        create_to_referrals_button(),
        create_to_help_button(),
        create_to_faq_button(),
        create_to_cheques_button(),
        create_to_my_bots_button(),
        width=2,
    )

    if is_admin:
        builder.row(create_to_admin_panel_button())

    return builder.as_markup()


def create_back_to_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        create_to_main_menu_button(),
    )

    return builder.as_markup()


def create_main_menu_button_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=tm.button.main_menu()),
            ]
        ],
        resize_keyboard=True,
    )
