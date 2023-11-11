from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def _create_referral_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="👛 Кошелёк",
            callback_data="wallet",
        ),
        InlineKeyboardButton(
            text="💡 FAQ-Помощь",
            callback_data="faq-help",
        ),
        InlineKeyboardButton(
            text="🤖 Мои боты",
            callback_data="my_bots",
        ),
        InlineKeyboardButton(
            text="📖 Главное меню",
            callback_data="main_menu",
        ),
    )

    builder.adjust(2, 2)

    return builder.as_markup()


referral_keyboard = _create_referral_keyboard()
