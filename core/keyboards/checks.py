from typing import Any, Dict, List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.callback_factories.checks import (
    CheckAction,
    CheckCallbackData,
    CheckType,
    SubscriptionType,
)
from core.config import config
from .main_menu import to_main_menu_button


def _create_choose_check_type_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Персональный чек",
            callback_data=CheckCallbackData(
                action=CheckAction.choose_action,
                type=CheckType.personal,
            ).pack(),
        ),
        InlineKeyboardButton(
            text="Мульти-чек",
            callback_data=CheckCallbackData(
                action=CheckAction.choose_action,
                type=CheckType.multi,
            ).pack(),
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text="📖 Главное меню",
            callback_data="main_menu",
        )
    )

    return builder.as_markup()


def create_choose_action_keyboard(
    data: CheckCallbackData,
    checks_count: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Создать чек",
            callback_data=data.model_copy(
                update={"action": CheckAction.get_amount}
            ).pack(),
        ),
        InlineKeyboardButton(
            text=f"Мои чеки({checks_count})",
            callback_data=data.model_copy(
                update={"action": CheckAction.view_checks}
            ).pack(),
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data=data.model_copy(
                update={"action": CheckAction.choose_type}
            ).pack(),
        )
    )

    return builder.as_markup()


def _create_no_balance_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Пополнить баланс",
            callback_data="wallet",
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data=CheckCallbackData(
                action=CheckAction.choose_action
            ).pack(),
        )
    )

    return builder.as_markup()


def create_get_sum_keyboard(
    data: CheckCallbackData,
    balance: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=f"Минимум {config.CHECK_MIN_SUM} руб",
            callback_data=data.model_copy(
                update={"amount": config.CHECK_MIN_SUM}
            ).pack(),
        ),
        InlineKeyboardButton(
            text=f"Максимум {balance} руб",
            callback_data=data.model_copy(update={"amount": balance}).pack(),
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data=data.model_copy(
                update={"action": CheckAction.choose_action}
            ).pack(),
        )
    )

    return builder.as_markup()


def create_confirm_keyboard(
    data: CheckCallbackData,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Отклонить",
            callback_data=data.model_copy(
                update={"action": CheckAction.choose_type}
            ).pack(),
        ),
        InlineKeyboardButton(
            text="Подтвердить",
            callback_data=data.model_copy(
                update={"action": CheckAction.create}
            ).pack(),
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text="Изменить сумму",
            callback_data=data.model_copy(
                update={"action": CheckAction.get_amount}
            ).pack(),
        ),
    )

    if data.type == CheckType.multi:
        builder.row(
            InlineKeyboardButton(
                text="Изменить количество",
                callback_data=data.model_copy(
                    update={"action": CheckAction.get_quantity}
                ).pack(),
            ),
        )

    return builder.as_markup()


def create_checks_keyboard(
    data: CheckCallbackData, checks: List[Any]
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for check in checks:
        builder.row(
            InlineKeyboardButton(
                text=str(check[2]),
                callback_data=data.model_copy(
                    update={"action": CheckAction.view_check, "id": check[0]}
                ).pack(),
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data=data.model_copy(
                update={"action": CheckAction.choose_action}
            ).pack(),
        )
    )

    return builder.as_markup()


def create_edit_check_keyboard(
    data: CheckCallbackData,
    link: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="💵 Отправить",
            switch_inline_query=link,
        )
    )

    if data.type == CheckType.multi:
        builder.row(
            InlineKeyboardButton(
                text="Добавить подписку",
                callback_data=data.model_copy(
                    update={"action": CheckAction.choose_subscription_type}
                ).pack(),
            ),
            InlineKeyboardButton(
                text="Подписки",
                callback_data=data.model_copy(
                    update={"action": CheckAction.view_subscriptions}
                ).pack(),
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text="Удалить",
            callback_data=data.model_copy(
                update={"action": CheckAction.delete}
            ).pack(),
        ),
    ).row(
        InlineKeyboardButton(
            text="Назад",
            callback_data=data.model_copy(
                update={"action": CheckAction.choose_action}
            ).pack(),
        ),
    ).row(
        to_main_menu_button,
    )

    return builder.as_markup()


def create_confirm_delete_keyboard(
    data: CheckCallbackData,
    yes_update_data: Dict[str, Any],
    no_update_data: Dict[str, Any],
    yes_text: str = "Да",
    no_text: str = "Нет",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=yes_text,
            callback_data=data.model_copy(
                # update={"action": CheckAction.delete_confirmed}
                update=yes_update_data,
            ).pack(),
        ),
        InlineKeyboardButton(
            text=no_text,
            callback_data=data.model_copy(
                # update={"action": CheckAction.view}
                update=no_update_data,
            ).pack(),
        ),
    )

    return builder.as_markup()


def create_delete_confirmed_keyboard(
    data: CheckCallbackData,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="К списку чеков",
            callback_data=data.model_copy(
                update={"action": CheckAction.view_checks}
            ).pack(),
        ),
    ).row(
        InlineKeyboardButton(
            text="Чеки",
            callback_data=data.model_copy(
                update={"action": CheckAction.choose_type}
            ).pack(),
        ),
    ).row(
        InlineKeyboardButton(
            text="📖 Главное меню",
            callback_data="main_menu",
        )
    )

    return builder.as_markup()


def create_choose_subscription_type_keyboard(
    data: CheckCallbackData,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="Канал",
            callback_data=data.model_copy(
                update={
                    "subscription_type": SubscriptionType.channel,
                    "action": CheckAction.get_chat_link,
                }
            ).pack(),
        ),
        InlineKeyboardButton(
            text="Публичная группа",
            callback_data=data.model_copy(
                update={
                    "subscription_type": SubscriptionType.public_group,
                    "action": CheckAction.get_chat_link,
                }
            ).pack(),
        ),
        InlineKeyboardButton(
            text="Приватная группа",
            callback_data=data.model_copy(
                update={
                    "subscription_type": SubscriptionType.private_group,
                    "action": CheckAction.get_chat_link,
                }
            ).pack(),
        ),
        InlineKeyboardButton(
            text="Назад",
            callback_data=data.model_copy(
                update={"action": CheckAction.view_check}
            ).pack(),
        ),
    )

    builder.adjust(1)

    return builder.as_markup()


def create_check_subscriptions_keyboard(
    data: CheckCallbackData,
    subscriptions: List[Any],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for subscription in subscriptions:
        builder.row(
            InlineKeyboardButton(
                text=str(subscription[2]),
                callback_data=data.model_copy(
                    update={
                        "action": CheckAction.view_subscription,
                        "chat_id": subscription[1],
                    }
                ).pack(),
            ),
            InlineKeyboardButton(
                text="Удалить",
                callback_data=data.model_copy(
                    update={
                        "action": CheckAction.delete_subscription,
                        "chat_id": subscription[1],
                    }
                ).pack(),
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text="Добавить",
            callback_data=data.model_copy(
                update={
                    "action": CheckAction.choose_subscription_type,
                }
            ).pack(),
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data=data.model_copy(
                update={
                    "action": CheckAction.view_check,
                }
            ).pack(),
        )
    )

    return builder.as_markup(resize_keyboard=True)


choose_check_type_keyboard = _create_choose_check_type_keyboard()
no_balance_keyboard = _create_no_balance_keyboard()
