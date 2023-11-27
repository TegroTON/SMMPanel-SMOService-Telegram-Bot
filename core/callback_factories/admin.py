from enum import IntEnum, auto

from aiogram.enums import ParseMode
from aiogram.filters.callback_data import CallbackData

from core.callback_factories.pagination import PaginationCallbackData
from core.service_provider.order_status import OrderStatus


class AdminAction(IntEnum):
    admin_menu = auto()
    view_orders = auto()
    view_wallets = auto()
    view_checks = auto()
    view_bots = auto()
    view_paylinks = auto()
    manage_locales = auto()
    download_locales = auto()
    upload_locales = auto()
    reload_locales = auto()
    broadcast_choose_format = auto()
    broadcast_get_message = auto()
    broadcast_get_message_for_copy = auto()
    broadcast_send = auto()
    broadcast_send_copy = auto()


class AdminCallbackData(CallbackData, prefix="adm"):
    action: AdminAction
    parse_mode: ParseMode | None = None


class ServiceAction(IntEnum):
    view = auto()
    toggle_service = auto()
    parse = auto()


class ServiceCallbackData(CallbackData, prefix="srvc"):
    action: ServiceAction = ServiceAction.view
    service_name: str | None = None


class AdminOrdersAction(IntEnum):
    view_orders = auto()
    view_order = auto()
    start_order = auto()
    cancel_order = auto()
    update_order_status = auto()
    set_status_filter = auto()
    toggle_status = auto()
    set_user_id_filter = auto()
    reset_filter = auto()


class AdminOrdersCallbackData(PaginationCallbackData, prefix="dm_rdrs"):
    action: AdminOrdersAction = AdminOrdersAction.view_orders
    order_id: int | None = None
    order_status: OrderStatus | None = None
    toggle_status: OrderStatus | None = None
