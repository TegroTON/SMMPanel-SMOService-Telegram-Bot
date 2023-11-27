from typing import Any, Dict, List

from aiogram.enums.parse_mode import ParseMode
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.callback_factories.admin import (
    AdminAction,
    AdminCallbackData,
    AdminOrdersAction,
    AdminOrdersCallbackData,
    ServiceAction,
    ServiceCallbackData,
)
from core.config import config
from core.service_provider.order_status import OrderStatus
from core.service_provider.provider import ServiceProvider
from core.text_manager import text_manager as tm

from .utils import (
    create_orders_buttons,
    create_pagination_buttons,
    create_to_admin_panel_button,
    create_to_main_menu_button,
)


def create_reset_filter_button(
    data: AdminCallbackData,
) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text="🔎 Сбросить фильтры.",
        callback_data=data.model_copy(
            update={"action": AdminOrdersAction.reset_filter},
        ).pack(),
    )


def create_admin_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="🛒 Управление заказами.",
            callback_data=AdminOrdersCallbackData(
                action=AdminOrdersAction.view_orders,
            ).pack(),
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text="🔧 Управление сервисами.",
            callback_data=ServiceCallbackData().pack(),
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text="📝 Управление текстами.",
            callback_data=AdminCallbackData(
                action=AdminAction.manage_locales,
            ).pack(),
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="✉️ Рассылка",
            callback_data=AdminCallbackData(
                action=AdminAction.broadcast_choose_format,
            ).pack(),
        )
    )

    builder.row(
        create_to_main_menu_button(),
    )

    return builder.as_markup()


def create_services_keyboard(
    services: List[ServiceProvider],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        *[
            InlineKeyboardButton(
                text=(
                    f"{service.name}"
                    f" - [{'on' if service.is_active else 'off'}]"
                ),
                callback_data=ServiceCallbackData(
                    action=ServiceAction.toggle_service,
                    service_name=service.name,
                ).pack(),
            )
            for service in services
        ]
    )

    builder.row(
        InlineKeyboardButton(
            text="Обновить активные сервисы",
            callback_data=ServiceCallbackData(
                action=ServiceAction.parse,
            ).pack(),
        ),
    )

    builder.row(
        create_to_admin_panel_button(),
    )

    return builder.as_markup()


def create_orders_list_keyboard(
    data: AdminCallbackData,
    orders: List[dict],
    filters_data: Dict[str, Any],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        *[
            InlineKeyboardButton(
                text=(
                    f"{OrderStatus(key).name_with_icon_ru} [{'on' if value else 'off'}]"  # noqa
                ),
                callback_data=data.model_copy(
                    update={
                        "action": AdminOrdersAction.toggle_status,
                        "toggle_status": OrderStatus(key),
                    }
                ).pack(),
            )
            for key, value in filters_data["statuses"].items()
        ],
        width=2,
    )

    builder.row(
        create_reset_filter_button(data=data),
    )

    has_next_page = False
    if len(orders) > config.PAGINATION_CATEGORIES_PER_PAGE:
        orders = orders[: config.PAGINATION_CATEGORIES_PER_PAGE]
        has_next_page = True

    builder.row(
        *create_orders_buttons(
            data=data.model_copy(
                update={
                    "action": AdminOrdersAction.view_order,
                }
            ),
            orders=orders,
        ),
        width=1,
    )

    builder.row(
        *create_pagination_buttons(
            data=data,
            has_next_page=has_next_page,
        )
    )

    builder.row(
        create_to_admin_panel_button(),
    )

    return builder.as_markup()


def create_manage_order_keyboard(
    data: AdminOrdersCallbackData,
    order_id: int,
    order_status: OrderStatus,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    buttons = []

    if order_status == OrderStatus.NEW:
        buttons.append(
            InlineKeyboardButton(
                text="🚀 Запустить",
                callback_data=data.model_copy(
                    update={
                        "action": AdminOrdersAction.start_order,
                    }
                ).pack(),
            )
        )
        buttons.append(
            InlineKeyboardButton(
                text="🛑 Отменить",
                callback_data=data.model_copy(
                    update={
                        "action": AdminOrdersAction.cancel_order,
                    }
                ).pack(),
            )
        )

    if order_status in [OrderStatus.IN_PROGRESS, OrderStatus.STARTING]:
        buttons.append(
            InlineKeyboardButton(
                text="🔄 Обновить статус",
                callback_data=data.model_copy(
                    update={
                        "action": AdminOrdersAction.update_order_status,
                        "order_status": order_status,
                    }
                ).pack(),
            )
        )

    builder.row(*buttons)

    builder.row(
        InlineKeyboardButton(
            text=tm.button.back(),
            callback_data=data.model_copy(
                update={"action": AdminOrdersAction.view_orders},
            ).pack(),
        ),
        create_to_admin_panel_button(),
        width=1,
    )

    return builder.as_markup()


def create_manage_locales_keyboard(
    data: AdminCallbackData,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="📥 Скачать",
            callback_data=data.model_copy(
                update={
                    "action": AdminAction.download_locales,
                }
            ).pack(),
        ),
        InlineKeyboardButton(
            text="📤 Загрузить",
            callback_data=data.model_copy(
                update={
                    "action": AdminAction.upload_locales,
                }
            ).pack(),
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text="♻️ Обновить текст",
            callback_data=data.model_copy(
                update={
                    "action": AdminAction.reload_locales,
                }
            ).pack(),
        )
    )

    builder.row(
        create_to_admin_panel_button(),
    )

    return builder.as_markup()


def create_choose_format_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=ParseMode.HTML.value,
            callback_data=AdminCallbackData(
                action=AdminAction.broadcast_get_message,
                parse_mode=ParseMode.HTML,
            ).pack(),
        ),
        InlineKeyboardButton(
            text=ParseMode.MARKDOWN.value,
            callback_data=AdminCallbackData(
                action=AdminAction.broadcast_get_message,
                parse_mode=ParseMode.MARKDOWN,
            ).pack(),
        ),
        InlineKeyboardButton(
            text=tm.button.original(),
            callback_data=AdminCallbackData(
                action=AdminAction.broadcast_get_message,
                parse_mode=None,
            ).pack(),
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text="📋 Копия сообщения",
            callback_data=AdminCallbackData(
                action=AdminAction.broadcast_get_message_for_copy,
            ).pack(),
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=tm.button.back(),
            callback_data=AdminCallbackData(
                action=AdminAction.admin_menu,
            ).pack(),
        ),
    )

    return builder.as_markup()
