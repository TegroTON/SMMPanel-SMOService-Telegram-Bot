from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    buttons = [
        ("🔥 Новый заказ", "new_order"),
        ("👛 Кошелёк", "wallet"),
        ("💰 Рефералы", "earn"),
        ("🦋 Чеки", "check"),
        ("🤖 Мои Боты", "my_bots"),
    ]

    if is_admin:
        buttons.append(("Админ-панель", "admin"))

    for button in buttons:
        builder.button(
            text=button[0],
            callback_data=button[1],
        )

    builder.adjust(1, 2)

    return builder.as_markup(resize_keyboard=True)


def create_back_to_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        to_main_menu_button,
    )

    return builder.as_markup()


to_main_menu_button = InlineKeyboardButton(
    text="📖 Главное меню",
    callback_data="main_menu",
)

back_to_main_menu_keyboard = create_back_to_main_menu_keyboard()
