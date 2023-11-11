from typing import List, Tuple
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.callback_factories.my_orders import (
    MyOrdersAction,
    MyOrdersCallbackData,
)

from core.callback_factories.wallet import WalletAction, WalletCallbackData
from core.config import config


def _create_wallet_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="💳 Пополнить баланс",
            callback_data=WalletCallbackData(
                action=WalletAction.replenish
            ).pack(),
        ),
        InlineKeyboardButton(
            text="📨 История операций",
            callback_data=WalletCallbackData(
                action=WalletAction.history
            ).pack(),
        ),
        InlineKeyboardButton(
            text="📋 Мои заказы",
            callback_data=MyOrdersCallbackData(
                action=MyOrdersAction.VIEW_ORDERS
            ).pack(),
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

    builder.adjust(1, 2, 1)

    return builder.as_markup()


def _create_replenish_amount_keyboard():
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
            text="Назад",
            callback_data=WalletCallbackData(
                action=WalletAction.choose_action,
            ).pack(),
        )
    )

    builder.adjust(3, 3, 1)

    return builder.as_markup()


def _create_history_keyboard() -> InlineKeyboardMarkup:
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
            text="Назад",
            callback_data=WalletCallbackData(
                action=WalletAction.choose_action
            ).pack(),
        )
    )

    return builder.as_markup()


def create_pay_keyboard(data: List[Tuple[str, str]]):
    builder = InlineKeyboardBuilder()

    for title, url in data:
        builder.row(
            InlineKeyboardButton(
                text=title,
                url=url,
            )
        )

    return builder.as_markup()


wallet_keyboard = _create_wallet_keyboard()
choose_replenish_amount_keyboard = _create_replenish_amount_keyboard()
history_keyboard = _create_history_keyboard()
