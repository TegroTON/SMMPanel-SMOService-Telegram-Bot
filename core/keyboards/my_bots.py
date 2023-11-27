from typing import Any, Dict, List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.callback_factories.my_bots import MyBotAction, MyBotCallbackData
from core.text_manager import text_manager as tm

from .utils import (
    create_to_main_menu_button,
    create_to_my_bots_button,
    create_to_referrals_button,
)


def create_manage_bots_keyboard(
    bots_data: List[Dict[str, Any]]
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for bot_data in bots_data:
        text = tm.button.bot_in_list().format(
            bot_username=bot_data["bot_username"]
        )
        if "unauthorized" in bot_data:
            text = f"{text} [Не авторизован]"
        if "current" in bot_data:
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
            text=tm.button.bot_create(),
            callback_data=MyBotCallbackData(
                action=MyBotAction.create_bot,
            ).pack(),
        ),
    )

    builder.row(
        create_to_referrals_button(),
        create_to_main_menu_button(),
    )

    return builder.as_markup()


def create_manage_bot_keyboard(
    data: MyBotCallbackData,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=tm.button.remove(),
            callback_data=MyBotCallbackData(
                action=MyBotAction.delete_bot,
                bot_id=data.bot_id,
            ).pack(),
        ),
    )

    builder.row(
        create_to_my_bots_button(),
    ),

    return builder.as_markup()


def create_delete_confirm_keyboard(
    data: MyBotCallbackData,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=tm.button.yes(),
            callback_data=MyBotCallbackData(
                action=MyBotAction.delete_confirmed,
                bot_id=data.bot_id,
            ).pack(),
        ),
        InlineKeyboardButton(
            text=tm.button.no(),
            callback_data=MyBotCallbackData(
                action=MyBotAction.view_bot,
                bot_id=data.bot_id,
            ).pack(),
        ),
    )

    return builder.as_markup()
