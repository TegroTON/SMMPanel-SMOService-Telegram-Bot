from typing import Dict
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.callback_factories.my_orders import (
    MyOrdersAction,
    MyOrdersCallbackData,
)

from core.callback_factories.wallet import WalletAction, WalletCallbackData
from core.config import config
from core.text_manager import text_manager as tm


def create_wallet_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=tm.button.replenish(),
            callback_data=WalletCallbackData(
                action=WalletAction.replenish
            ).pack(),
        ),
        InlineKeyboardButton(
            text=tm.button.history(),
            callback_data=WalletCallbackData(
                action=WalletAction.history
            ).pack(),
        ),
        InlineKeyboardButton(
            text=tm.button.my_orders(),
            callback_data=MyOrdersCallbackData(
                action=MyOrdersAction.VIEW_ORDERS
            ).pack(),
        ),
        InlineKeyboardButton(
            text=tm.button.referrals(),
            callback_data="earn",
        ),
        InlineKeyboardButton(
            text=tm.button.main_menu(),
            callback_data="main_menu",
        ),
    )

    builder.adjust(2, 2, 1)

    return builder.as_markup()


def create_choose_replenish_amount_keyboard():
    builder = InlineKeyboardBuilder()

    for amount in config.REPLENISH_AMOUNT_VARIANTS:
        builder.add(
            InlineKeyboardButton(
                text=f"{amount} руб",
                callback_data=WalletCallbackData(
                    action=WalletAction.get_amount,
                    amount=amount,
                ).pack(),
            )
        )

    builder.row(
        InlineKeyboardButton(
            text=tm.button.back(),
            callback_data=WalletCallbackData(
                action=WalletAction.choose_action,
            ).pack(),
        )
    )

    builder.adjust(3, 3, 1)

    return builder.as_markup()


def create_history_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Скачать историю операций",
            callback_data=WalletCallbackData(
                action=WalletAction.history_document
            ).pack(),
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=tm.button.back(),
            callback_data=WalletCallbackData(
                action=WalletAction.choose_action
            ).pack(),
        )
    )

    return builder.as_markup()


def create_pay_keyboard(
    paylinks: Dict[str, str],
):
    builder = InlineKeyboardBuilder()

    for title, paylink in paylinks.items():
        if not paylink:
            continue
        builder.row(
            InlineKeyboardButton(
                text=title,
                url=paylink,
            )
        )

    builder.row(
        InlineKeyboardButton(
            text=tm.button.back(),
            callback_data=WalletCallbackData(
                action=WalletAction.choose_action,
            ).pack(),
        )
    )

    return builder.as_markup()
