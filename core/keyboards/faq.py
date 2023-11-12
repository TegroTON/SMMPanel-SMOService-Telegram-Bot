from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def _create_faq_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="👛 Кошелёк",
            callback_data="wallet",
        ),
        InlineKeyboardButton(
            text="💰 Рефералы",
            callback_data="earn",
        ),
        InlineKeyboardButton(
            text="📖 Главное меню",
            callback_data="main_menu",
        ),
    )

    builder.adjust(2, 1)

    return builder.as_markup()


faq_keyboard = _create_faq_keyboard()
