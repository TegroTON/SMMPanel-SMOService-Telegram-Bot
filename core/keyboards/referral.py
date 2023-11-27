from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.keyboards.utils import (
    create_to_main_menu_button,
    create_to_my_bots_button,
    create_to_wallet_button,
)


def create_referral_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        create_to_wallet_button(),
        create_to_my_bots_button(),
        create_to_main_menu_button(),
    )

    builder.adjust(2, 2)

    return builder.as_markup()
