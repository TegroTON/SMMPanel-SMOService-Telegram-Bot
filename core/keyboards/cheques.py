from typing import Any, Dict, List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.callback_factories.cheques import (
    CheckSubscribesCallbackData,
    ChequeAction,
    ChequeCallbackData,
    ChequeType,
    SubscriptionType,
)
from core.config import config
from .utils import create_to_main_menu_button
from core.text_manager import text_manager as tm


def create_cheque_choose_action_keyboard(
    cheques_count: int,
    multi_cheques_count: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    data = ChequeCallbackData()

    builder.row(
        InlineKeyboardButton(
            text=tm.button.cheques_create_check(),
            callback_data=ChequeCallbackData(
                action=ChequeAction.get_amount,
                type=ChequeType.personal,
            ).pack(),
        ),
        InlineKeyboardButton(
            text=tm.button.cheques_create_multi_check(),
            callback_data=ChequeCallbackData(
                action=ChequeAction.get_amount,
                type=ChequeType.multi,
            ).pack(),
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=tm.button.cheques_with_count().format(count=cheques_count),
            callback_data=data.model_copy(
                update={
                    "action": ChequeAction.view_checks,
                    "type": ChequeType.personal,
                }
            ).pack(),
        ),
        InlineKeyboardButton(
            text=tm.button.cheques_multi_with_count().format(
                count=multi_cheques_count
            ),
            callback_data=data.model_copy(
                update={
                    "action": ChequeAction.view_checks,
                    "type": ChequeType.multi,
                }
            ).pack(),
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=tm.button.back(),
            callback_data="main_menu",
        )
    )

    return builder.as_markup()


def create_no_balance_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=tm.button.replenish_balance(),
            callback_data="wallet",
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=tm.button.cheques(),
            callback_data=ChequeCallbackData(
                action=ChequeAction.choose_action
            ).pack(),
        )
    )

    return builder.as_markup()


def create_get_sum_keyboard(
    data: ChequeCallbackData,
    balance: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=tm.button.cheques_min_sum().format(
                min_sum=config.CHEQUE_MIN_SUM
            ),
            callback_data=data.model_copy(
                update={"amount": config.CHEQUE_MIN_SUM}
            ).pack(),
        ),
        InlineKeyboardButton(
            text=tm.button.cheques_max_sum().format(max_sum=balance),
            callback_data=data.model_copy(update={"amount": balance}).pack(),
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=tm.button.cheques(),
            callback_data=data.model_copy(
                update={"action": ChequeAction.choose_action}
            ).pack(),
        )
    )

    return builder.as_markup()


def create_get_quantity_keyboard(
    data: ChequeCallbackData,
    max_quantity: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=tm.button.cheques_min_quantity().format(
                min_quantity=config.CHEQUE_MIN_QUANTITY,
            ),
            callback_data=data.model_copy(
                update={
                    "action": ChequeAction.confirm,
                    "quantity": config.CHEQUE_MIN_QUANTITY,
                },
            ).pack(),
        ),
        InlineKeyboardButton(
            text=tm.button.cheques_max_quantity().format(
                max_quantity=max_quantity
            ),
            callback_data=data.model_copy(
                update={
                    "action": ChequeAction.confirm,
                    "quantity": max_quantity,
                },
            ).pack(),
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=tm.button.change_amount(),
            callback_data=data.model_copy(
                update={"action": ChequeAction.get_amount}
            ).pack(),
        )
    )

    return builder.as_markup()


def create_confirm_keyboard(
    data: ChequeCallbackData,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=tm.button.accept(),
            callback_data=data.model_copy(
                update={"action": ChequeAction.create}
            ).pack(),
        ),
        InlineKeyboardButton(
            text=tm.button.decline(),
            callback_data=data.model_copy(
                update={"action": ChequeAction.choose_action}
            ).pack(),
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=tm.button.change_amount(),
            callback_data=data.model_copy(
                update={"action": ChequeAction.get_amount}
            ).pack(),
        ),
    )

    if data.type == ChequeType.multi:
        builder.row(
            InlineKeyboardButton(
                text=tm.button.change_quantity(),
                callback_data=data.model_copy(
                    update={"action": ChequeAction.get_quantity}
                ).pack(),
            ),
        )

    return builder.as_markup()


def create_checks_keyboard(
    data: ChequeCallbackData, checks: List[Any]
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for check in checks:
        if check[7] == "personal":
            text = f"{check[2]}"
        else:
            text = f"{check[2]} руб {check[3]}/{check[9]}"
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=data.model_copy(
                    update={"action": ChequeAction.view_check, "id": check[0]}
                ).pack(),
            )
        )

    builder.adjust(2)

    builder.row(
        InlineKeyboardButton(
            text=tm.button.back(),
            callback_data=data.model_copy(
                update={"action": ChequeAction.choose_action}
            ).pack(),
        )
    )

    return builder.as_markup()


def create_edit_cheque_keyboard(
    data: ChequeCallbackData,
    link: str,
    is_fully_activated: bool,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if not is_fully_activated:
        builder.row(
            InlineKeyboardButton(
                text=tm.button.send_cheque(),
                switch_inline_query=link,
            )
        )

    if data.type == ChequeType.multi and not is_fully_activated:
        builder.row(
            # InlineKeyboardButton(
            #     text=tm.button.add_subscribe(),
            #     callback_data=data.model_copy(
            #         update={"action": ChequeAction.choose_subscription_type}
            #     ).pack(),
            # ),
            InlineKeyboardButton(
                text=tm.button.subscribes(),
                callback_data=data.model_copy(
                    update={"action": ChequeAction.view_subscriptions}
                ).pack(),
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text=tm.button.remove(),
            callback_data=data.model_copy(
                update={"action": ChequeAction.delete}
            ).pack(),
        ),
    ).row(
        InlineKeyboardButton(
            text=tm.button.back(),
            callback_data=data.model_copy(
                update={"action": ChequeAction.view_checks}
            ).pack(),
        ),
    ).row(
        create_to_main_menu_button(),
    )

    return builder.as_markup()


def create_confirm_delete_keyboard(
    data: ChequeCallbackData,
    yes_update_data: Dict[str, Any],
    no_update_data: Dict[str, Any],
    yes_text: str | None = None,
    no_text: str | None = None,
) -> InlineKeyboardMarkup:
    if not yes_text:
        yes_text = tm.button.yes()
    if not no_text:
        no_text = tm.button.no()

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=yes_text,
            callback_data=data.model_copy(
                update=yes_update_data,
            ).pack(),
        ),
        InlineKeyboardButton(
            text=no_text,
            callback_data=data.model_copy(
                update=no_update_data,
            ).pack(),
        ),
    )

    return builder.as_markup()


def create_delete_confirmed_keyboard(
    data: ChequeCallbackData,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=tm.button.cheques_list(),
            callback_data=data.model_copy(
                update={"action": ChequeAction.view_checks}
            ).pack(),
        ),
    ).row(
        InlineKeyboardButton(
            text=tm.button.cheques(),
            callback_data=data.model_copy(
                update={"action": ChequeAction.choose_action}
            ).pack(),
        ),
    ).row(
        InlineKeyboardButton(
            text=tm.button.main_menu(),
            callback_data="main_menu",
        )
    )

    return builder.as_markup()


def create_choose_subscription_type_keyboard(
    data: ChequeCallbackData,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text=tm.button.subscribe_channel(),
            callback_data=data.model_copy(
                update={
                    "subscription_type": SubscriptionType.channel,
                    "action": ChequeAction.get_chat_link,
                }
            ).pack(),
        ),
        InlineKeyboardButton(
            text=tm.button.subscribe_group(),
            callback_data=data.model_copy(
                update={
                    "subscription_type": SubscriptionType.public_group,
                    "action": ChequeAction.get_chat_link,
                }
            ).pack(),
        ),
        InlineKeyboardButton(
            text=tm.button.subscribe_private_group(),
            callback_data=data.model_copy(
                update={
                    "subscription_type": SubscriptionType.private_group,
                    "action": ChequeAction.get_chat_link,
                }
            ).pack(),
        ),
    )

    builder.add(
        InlineKeyboardButton(
            text=tm.button.back(),
            callback_data=data.model_copy(
                update={"action": ChequeAction.view_subscriptions}
            ).pack(),
        ),
    )

    builder.adjust(1)

    return builder.as_markup()


def create_check_subscriptions_keyboard(
    data: ChequeCallbackData,
    subscriptions: List[Any],
    subscribes_left: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for subscription in subscriptions:
        builder.row(
            InlineKeyboardButton(
                text=str(subscription[2]),
                callback_data=data.model_copy(
                    update={
                        "action": ChequeAction.view_subscription,
                        "chat_id": subscription[1],
                    }
                ).pack(),
            ),
            InlineKeyboardButton(
                text=tm.button.remove(),
                callback_data=data.model_copy(
                    update={
                        "action": ChequeAction.delete_subscription,
                        "chat_id": subscription[1],
                    }
                ).pack(),
            ),
        )

    if subscribes_left:
        builder.row(
            InlineKeyboardButton(
                text=tm.button.add_subscribe(),
                callback_data=data.model_copy(
                    update={
                        "action": ChequeAction.choose_subscription_type,
                    }
                ).pack(),
            )
        )

    builder.row(
        InlineKeyboardButton(
            text=tm.button.back(),
            callback_data=data.model_copy(
                update={
                    "action": ChequeAction.view_check,
                }
            ).pack(),
        )
    )

    return builder.as_markup(resize_keyboard=True)


def create_check_subscribes_keyboard(
    cheque_number: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=tm.button.check_subscribes(),
            callback_data=CheckSubscribesCallbackData(
                cheque_number=cheque_number
            ).pack(),
        )
    )

    return builder.as_markup()
