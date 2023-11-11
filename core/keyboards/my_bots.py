from typing import Any, Dict, List
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.callback_factories.my_bots import MyBotAction, MyBotCallbackData

from .main_menu import to_main_menu_button


def create_manage_bots_keyboard(
    bots_data: List[Dict[str, Any]]
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for bot_data in bots_data:
        text = f"@{bot_data['username']}"
        if bot_data["current"]:
            text = f"{text} [Текущий]"
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=MyBotCallbackData(
                    action=MyBotAction.view_bot,
                    bot_id=bot_data["id"],
                ).pack(),
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text="Создать",
            callback_data=MyBotCallbackData(
                action=MyBotAction.create_bot,
            ).pack(),
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text="💰 Рефералы",
            callback_data="earn",
        ),
        to_main_menu_button,
    )

    return builder.as_markup()


def create_manage_bot_keyboard(
    data: MyBotCallbackData,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Удалить",
            callback_data=MyBotCallbackData(
                action=MyBotAction.delete_bot,
                bot_id=data.bot_id,
            ).pack(),
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text="К ботам",
            callback_data=MyBotCallbackData(
                action=MyBotAction.view_bots,
            ).pack(),
        )
    ),

    return builder.as_markup()


def create_delete_confirm_keyboard(
    data: MyBotCallbackData,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✅ Да",
            callback_data=MyBotCallbackData(
                action=MyBotAction.delete_confirmed,
                bot_id=data.bot_id,
            ).pack(),
        ),
        InlineKeyboardButton(
            text="❌ Нет",
            callback_data=MyBotCallbackData(
                action=MyBotAction.view_bot,
                bot_id=data.bot_id,
            ).pack(),
        ),
    )

    return builder.as_markup()
