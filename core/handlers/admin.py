import asyncio
import copy
import logging
import os
import subprocess
from typing import Callable

from aiogram import Bot, F, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums.parse_mode import ParseMode
from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramUnauthorizedError,
)
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.utils.i18n import get_i18n

import database as db
from core.callback_factories.admin import (
    AdminAction,
    AdminCallbackData,
    AdminOrdersAction,
    AdminOrdersCallbackData,
    ServiceAction,
    ServiceCallbackData,
)
from core.config import config
from core.filters import IsFilterUrl, IsFilterUserId, IsUserAdmin
from core.filters.orders_filters import IsFilterOrderId
from core.keyboards.admin import (
    create_admin_menu_keyboard,
    create_choose_format_keyboard,
    create_manage_locales_keyboard,
    create_manage_order_keyboard,
    create_orders_list_keyboard,
    create_services_keyboard,
)
from core.keyboards.utils import create_back_keyboard, create_confirm_keyboard
from core.service_provider.manager import provider_manager
from core.service_provider.order_status import OrderStatus
from core.service_provider.provider import ServiceParseError
from core.text_manager import text_manager as tm

logger = logging.getLogger(__name__)


class AdminOrdersState(StatesGroup):
    enter_filter = State()


class AdminLocalesState(StatesGroup):
    send_file = State()


class AdminBroadcastState(StatesGroup):
    enter_message = State()
    send_message_to_copy = State()


filters_default_data = {
    "statuses": {
        OrderStatus.PENDING_PAYMENT.value: True,
        OrderStatus.NEW.value: True,
        OrderStatus.IN_PROGRESS.value: True,
        OrderStatus.COMPLETED.value: True,
        OrderStatus.CANCELED.value: False,
        OrderStatus.PARTIAL.value: True,
    },
    "user_id": None,
    "link": None,
    "order_id": None,
    "callback_data": None,
    "message_id": None,
}


admin_router = Router()
admin_router.callback_query.filter(IsUserAdmin())
admin_router.message.filter(IsUserAdmin())


@admin_router.callback_query(
    or_f(
        (F.data == "admin_panel"),
        AdminCallbackData.filter(F.action == AdminAction.admin_menu),
    )
)
async def admin_panel_callback_handler(
    callback: CallbackQuery,
):
    await callback.message.edit_text(
        "<b>👨‍💻 Панель администратора</b>",
        reply_markup=create_admin_menu_keyboard(),
    )


@admin_router.callback_query(
    ServiceCallbackData.filter(
        F.action.in_({ServiceAction.view, ServiceAction.toggle_service})
    )
)
async def view_services_callback_handler(
    callback: CallbackQuery,
    callback_data: ServiceCallbackData,
):
    if callback_data.action == ServiceAction.toggle_service:
        provider_manager.toggle_service(callback_data.service_name)

    await callback.message.edit_text(
        text=(
            "<b>👨‍💻 Панель администратора\n   -> 🔧 Управление сервисами</b>\n"
            "[on] - сервис включен | [off] - сервис выключен\n"
            "Нажмите на сервис, чтобы изменить его состояние."
        ),
        reply_markup=create_services_keyboard(
            services=provider_manager.get_all_services_list(),
        ),
    )


@admin_router.callback_query(
    ServiceCallbackData.filter(F.action == ServiceAction.parse)
)
async def parse_services(
    callback: CallbackQuery,
    callback_data: ServiceCallbackData,
):
    tasks = []
    for provider in provider_manager.get_active_services_list():
        tasks.append(provider.parse_services())

    messages = []
    has_error = False
    for coroutine in asyncio.as_completed(tasks):
        try:
            service_name = await coroutine
            messages.append(
                f"Услуги <b>'{service_name}'</b> успешно обновлены.\n"
            )
        except ServiceParseError as error:
            messages.append(
                f"Не удалось обновить услуги <b>'{error.service_name}'</b> \n"
                f"Причина: {error.cause}!\n"
            )
            has_error = True

    results = "\n".join(messages)

    if has_error:
        await callback.message.answer(
            text=f"<b>Результаты:</b>\n\n{results}",
        )
    else:
        await callback.answer(
            text="Все услуги успешно обновлены!",
        )


@admin_router.callback_query(
    AdminOrdersCallbackData.filter(
        F.action.in_(
            {
                AdminOrdersAction.set_status_filter,
                AdminOrdersAction.toggle_status,
                AdminOrdersAction.view_orders,
            }
        )
    )
)
async def view_orders_callback_handler(
    callback: CallbackQuery,
    callback_data: AdminOrdersCallbackData,
    state: FSMContext,
):
    filters_data = await state.get_data()

    if not {"statuses", "user_id", "link", "callback_data"}.issubset(
        (filters_data.keys())
    ):
        filters_data = copy.deepcopy(filters_default_data)
        filters_data["callback_data"] = callback_data

    if callback_data.action == AdminOrdersAction.toggle_status:
        filters_data["statuses"][
            callback_data.toggle_status.value
        ] = not filters_data["statuses"][callback_data.toggle_status.value]

    statuses = [
        OrderStatus(key)
        for key, enabled in filters_data["statuses"].items()
        if enabled
    ]

    user_id_like = filters_data["user_id"]

    link_like = filters_data["link"]

    order_id_like = filters_data["order_id"]

    orders = db.get_orders_for_pagination(
        user_id_like=user_id_like,
        order_id_like=order_id_like,
        statuses=statuses,
        link_like=link_like,
        limit=config.PAGINATION_CATEGORIES_PER_PAGE,
        page=callback_data.page,
    )

    answer = await callback.message.edit_text(
        text=tm.message.admin_list_orders().format(
            user_id=filters_data["user_id"] or "",
            order_id=filters_data["order_id"] or "",
            link=filters_data["link"] or "",
        ),
        reply_markup=create_orders_list_keyboard(
            data=callback_data,
            orders=orders,
            filters_data=filters_data,
        ),
    )

    filters_data["message_id"] = answer.message_id

    await state.update_data(
        **filters_data,
    )

    await state.set_state(AdminOrdersState.enter_filter)


@admin_router.message(
    AdminOrdersState.enter_filter,
    or_f(
        IsFilterUserId(),
        IsFilterUrl(),
        IsFilterOrderId(),
    ),
)
async def set_filter_message_handler(
    message: Message,
    state: FSMContext,
    bot: Bot,
    user_id: int | None = None,
    link: str | None = None,
    order_id: int | None = None,
):
    if user_id:
        await state.update_data(
            user_id=user_id,
        )
    elif link:
        await state.update_data(
            link=link,
        )
    elif order_id:
        await state.update_data(
            order_id=order_id,
        )

    filters_data = await state.get_data()

    message_id = filters_data["message_id"]

    orders = db.get_orders_for_pagination(
        user_id_like=filters_data["user_id"],
        order_id_like=filters_data["order_id"],
        statuses=[
            OrderStatus(key)
            for key, enabled in filters_data["statuses"].items()
            if enabled
        ],
        link_like=filters_data["link"],
        limit=config.PAGINATION_CATEGORIES_PER_PAGE,
        page=filters_data["callback_data"].page,
    )

    await bot.edit_message_text(
        text=tm.message.admin_list_orders().format(
            user_id=filters_data["user_id"] or "",
            link=filters_data["link"] or "",
            order_id=filters_data["order_id"] or "",
        ),
        chat_id=message.chat.id,
        message_id=message_id,
        reply_markup=create_orders_list_keyboard(
            data=filters_data["callback_data"],
            orders=orders,
            filters_data=filters_data,
        ),
    )

    await message.delete()


@admin_router.message(
    AdminOrdersState.enter_filter,
)
async def set_filter_incorrect_message_handler(
    message: Message,
):
    await message.delete()


@admin_router.callback_query(
    AdminOrdersCallbackData.filter(
        F.action == AdminOrdersAction.reset_filter,
    )
)
async def reset_filters_callback_handler(
    callback: CallbackQuery,
    callback_data: AdminOrdersCallbackData,
    state: FSMContext,
):
    filters_data = await state.get_data()
    filters_data["callback_data"] = None
    filters_data["message_id"] = None

    if filters_data == filters_default_data:
        await callback.answer("Фильтры уже сброшены")
        return

    await state.set_data({})

    await callback.answer("Фильтры сброшены")

    await view_orders_callback_handler(
        callback=callback,
        callback_data=callback_data,
        state=state,
    )


@admin_router.callback_query(
    AdminOrdersCallbackData.filter(
        F.action.in_(
            {
                AdminOrdersAction.view_order,
                AdminOrdersAction.update_order_status,
                AdminOrdersAction.start_order,
                AdminOrdersAction.cancel_order,
            }
        )
    )
)
async def view_order_callback_handler(
    callback: CallbackQuery,
    callback_data: AdminOrdersCallbackData,
):
    order = db.get_order_by_id(callback_data.order_id)

    if (
        callback_data.action == AdminOrdersAction.update_order_status
        and callback_data.order_status == OrderStatus(order["status"])
    ):
        await provider_manager.check_order_status(
            order_id=order["id"],
            external_order_id=order["order_id"],
            service_name=order["service_provider"],
        )
        updated_order = db.get_order_by_id(callback_data.order_id)
        if callback_data.order_status == OrderStatus(updated_order["status"]):
            await callback.answer("Статус не изменился...")
            return

    elif (
        callback_data.action == AdminOrdersAction.start_order
        and OrderStatus(order["status"]) == OrderStatus.NEW
    ):
        await provider_manager.activate_order(
            order_id=order["id"],
            service_name=order["service_provider"],
        )
        order = db.get_order_by_id(callback_data.order_id)

        if callback_data.order_status == OrderStatus(order["status"]):
            await callback.answer("Не удалось активировать заказ...")
            return

    elif (
        callback_data.action == AdminOrdersAction.cancel_order
        and OrderStatus(order["status"]) == OrderStatus.NEW
    ):
        await provider_manager.cancel_order(
            order_id=order["id"],
        )
        order = db.get_order_by_id(callback_data.order_id)

        if callback_data.order_status == OrderStatus(order["status"]):
            await callback.answer("Не удалось отменить заказ...")
            return

    await callback.message.edit_text(
        text=(
            "<b>👨‍💻 Панель администратора</b>\n"
            "   <b>└ 🛒 Управление заказами</b>\n"
            "      <b>└ 🧾 Информация о заказе</b>\n"
            "\n"
            f"{order['name']}\n"
            f"User ID:    {order['user_id']}\n\n"
            f"ID:         {order['id']}\n"
            f"Export ID:  {order['order_id'] or 'Присваивается после оплаты'}"
            "\n"
            f"Статус:     {OrderStatus(order['status']).name_with_icon_ru}\n"
            f"Ссылка:\n   {order['url']}\n"
            f"Количество: {order['quantity']}\n"
            f"Стоимость:  {order['sum']}\n"
        ),
        reply_markup=create_manage_order_keyboard(
            data=callback_data,
            order_id=callback_data.order_id,
            order_status=OrderStatus(order["status"]),
        ),
    )


@admin_router.callback_query(
    AdminCallbackData.filter(
        F.action == AdminAction.manage_locales,
    )
)
async def manage_locales_callback_handler(
    callback: CallbackQuery,
    callback_data: AdminCallbackData,
):
    await callback.message.edit_text(
        text=(
            "<b>👨‍💻 Панель администратора</b>\n"
            "   <b>└ 📝 Управление локализацией</b>\n"
            "\n"
            "Для изменения текстовой информации бота, необходимо:\n"
            "1. Скачать файл локализации.\n"
            "2. Внести изменения. Это .po файл. изменения можно произвести"
            " вручную или с помощью программы <b>PoEdit</b>.\n"
            "3. Загрузить измененный файл.\n"
            "4. Нажать на кнопку <b>Обновить текст</b>.\n"
            "\n"
            "Если файл будет успешно обработан, то вы увидите уведомление.\n"
            "Если нет, то вы увидите сообщение об ошибке.\n"
        ),
        reply_markup=create_manage_locales_keyboard(
            data=callback_data,
        ),
    )


@admin_router.callback_query(
    AdminCallbackData.filter(
        F.action == AdminAction.download_locales,
    )
)
async def download_locales_callback_handler(
    callback: CallbackQuery,
):
    locales_file = FSInputFile("locales/ru_RU/LC_MESSAGES/messages.po")

    await callback.message.answer_document(
        document=locales_file,
    )


@admin_router.callback_query(
    AdminCallbackData.filter(
        F.action == AdminAction.upload_locales,
    )
)
async def upload_locales_callback_handler(
    callback: CallbackQuery,
    callback_data: AdminCallbackData,
    state: FSMContext,
):
    await callback.message.edit_text(
        text=(
            "<b>👨‍💻 Панель администратора</b>\n"
            "   <b>└ 📝 Управление локализацией</b>\n"
            "      <b>└ 📤 Загрузка локализации</b>\n"
            "\n"
            "Загрузите файл с локализацией в формате .po"
        ),
    )

    await state.set_state(AdminLocalesState.send_file)


@admin_router.message(
    AdminLocalesState.send_file,
)
async def send_locales_file(
    message: Message,
    state: FSMContext,
    bot: Bot,
):
    if not message.document:
        await message.reply("☝️ Это не файл!")
        await message.delete()
        return

    await state.set_state(None)

    await bot.download(
        message.document, "locales/ru_RU/LC_MESSAGES/messages.po.new"
    )

    result = subprocess.call(
        [
            "pybabel",
            "compile",
            "-d",
            "locales",
            "-D",
            "messages",
            "-i",
            "locales/ru_RU/LC_MESSAGES/messages.po.new",
            "-o",
            "locales/ru_RU/LC_MESSAGES/messages.mo.new",
        ]
    )

    if result != 0:
        if os.path.exists("locales/ru_RU/LC_MESSAGES/messages.po.new"):
            os.remove("locales/ru_RU/LC_MESSAGES/messages.po.new")
        if os.path.exists("locales/ru_RU/LC_MESSAGES/messages.mo.new"):
            os.remove("locales/ru_RU/LC_MESSAGES/messages.mo.new")

        await message.answer(
            text=(
                "☝️ Что-то пошло не так!\n"
                "🤔 Похоже вы загрузили неверный файл."
            )
        )
        await message.delete()
        return

    if os.path.exists("locales/ru_RU/LC_MESSAGES/messages.po.back"):
        os.remove("locales/ru_RU/LC_MESSAGES/messages.po.back")

    if os.path.exists("locales/ru_RU/LC_MESSAGES/messages.mo.new"):
        os.remove("locales/ru_RU/LC_MESSAGES/messages.mo.new")

    os.rename(
        "locales/ru_RU/LC_MESSAGES/messages.po",
        "locales/ru_RU/LC_MESSAGES/messages.po.back",
    )
    os.rename(
        "locales/ru_RU/LC_MESSAGES/messages.po.new",
        "locales/ru_RU/LC_MESSAGES/messages.po",
    )

    await message.answer(
        text=(
            "<b>👨‍💻 Панель администратора</b>\n"
            "   <b>└ 📝 Управление локализацией</b>\n"
            "      <b>└ 📤 Загрузка локализации</b>\n"
            "\n"
            "🎉 Локализация успешно загружена!\n"
        ),
        reply_markup=create_back_keyboard(
            text="📝 Управление локализацией",
            data=AdminCallbackData(
                action=AdminAction.manage_locales,
            ),
        ),
    )


@admin_router.callback_query(
    AdminCallbackData.filter(F.action == AdminAction.reload_locales),
)
async def reload_locales_callback_handler(
    callback: CallbackQuery,
):
    subprocess.call(["pybabel", "compile", "-d", "locales", "-D", "messages"])

    i18n = get_i18n()
    i18n.reload()

    await callback.answer("🎉 Локализация успешно обновлена!")


@admin_router.callback_query(
    AdminCallbackData.filter(
        F.action == AdminAction.broadcast_choose_format,
    )
)
async def broadcast_choose_format_callback_handler(
    callback: CallbackQuery,
):
    await callback.message.edit_text(
        text=(
            "<b>👨‍💻 Панель администратора</b>\n"
            "   <b>└ ✉️ Рассылка</b>\n"
            "      <b>└ 🖌️ Выбор форматирования</b>\n"
            "\n"
            "<b>'HTML'</b>, <b>'MARKDOWN'</b> - Можно отправить код, который будет парситься в соответствии с выбранным форматированием.\n"  # noqa
            "<b>'Как есть'</b> - Будет сохранено форматирование вашего сообщения.\n"  # noqa
            "<b>'Копия сообщения'</b> - Будет создана копия вашего сообщения. Можно разослать картинку, видео, стикер, документ, аудио.\n"  # noqa
            "\n"
            "👇 Выберите тип форматирования сообщения:"
        ),
        reply_markup=create_choose_format_keyboard(),
    )


@admin_router.callback_query(
    AdminCallbackData.filter(
        F.action == AdminAction.broadcast_get_message,
    )
)
async def broadcast_callback_handler(
    callback: CallbackQuery,
    callback_data: AdminCallbackData,
    state: FSMContext,
):
    state_data = await state.get_data()

    if "broadcast" in state_data and "header_id" in state_data["broadcast"]:
        await callback.bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=state_data["broadcast"].pop("header_id"),
        )

    state_data["broadcast"] = {"parse_mode": callback_data.parse_mode}

    parse_mode = (
        callback_data.parse_mode.value
        if callback_data.parse_mode
        else tm.button.original()
    )

    await callback.message.edit_text(
        text=(
            "<b>👨‍💻 Панель администратора</b>\n"
            "   <b>└ ✉️ Рассылка</b>\n"
            "\n"
            "Форматирование: 🖌️ {parse_mode}\n"
            "Отправьте сообщение для рассылки.\n"
        ).format(
            parse_mode=parse_mode,
        ),
        reply_markup=create_back_keyboard(
            data=callback_data.model_copy(
                update={"action": AdminAction.broadcast_choose_format}
            ),
        ),
    )

    await state.set_data(state_data)
    await state.set_state(AdminBroadcastState.enter_message)


@admin_router.callback_query(
    AdminCallbackData.filter(
        F.action == AdminAction.broadcast_get_message_for_copy,
    )
)
async def broadcast_get_message_for_copy_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.message.edit_text(
        text=(
            "<b>👨‍💻 Панель администратора</b>\n"
            "   <b>└ ✉️ Рассылка</b>\n"
            "\n"
            "Отправьте сообщение для рассылки.\n"
        ),
        reply_markup=create_back_keyboard(
            data=AdminCallbackData(
                action=AdminAction.broadcast_choose_format,
            ),
        ),
    )

    await state.set_state(AdminBroadcastState.send_message_to_copy)


@admin_router.message(
    AdminBroadcastState.send_message_to_copy,
    or_f(
        F.animation,
        F.audio,
        F.document,
        F.photo,
        F.sticker,
        F.story,
        F.video,
        F.video_note,
        F.voice,
        F.dice,
    ),
)
async def send_message_to_copy_handler(
    message: Message,
    state: FSMContext,
):
    await state.set_state(None)
    state_data = await state.get_data()

    state_data["broadcast"] = {
        "message_to_copy": {
            "from_chat_id": message.chat.id,
            "message_id": message.message_id,
        }
    }

    await state.set_data(state_data)

    await message.bot.copy_message(
        chat_id=message.chat.id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
    )

    await message.answer(
        text=(
            "<b>👨‍💻 Панель администратора</b>\n"
            "   <b>└ ✉️ Рассылка</b>\n"
            "      <b>└ Предпросмотр рассылки</b>\n"
            "\n"
            "Осуществить рассылку этого сообщения?\n"
        ),
        reply_markup=create_confirm_keyboard(
            accept_text=tm.button.accept(),
            accept_data=AdminCallbackData(
                action=AdminAction.broadcast_send_copy,
            ),
            decline_text=tm.button.decline(),
            decline_data=AdminCallbackData(
                action=AdminAction.broadcast_get_message_for_copy,
            ),
        ),
    )


@admin_router.message(AdminBroadcastState.enter_message)
async def enter_broadcast_message_handler(
    message: Message,
    state: FSMContext,
):
    state_data = await state.get_data()
    await state.set_state(None)

    parse_mode = state_data["broadcast"]["parse_mode"]

    broadcast_message = message.text if parse_mode else message.html_text

    header_message = await message.answer(
        text=(
            "<b>👨‍💻 Панель администратора</b>\n"
            "   <b>└ ✉️ Рассылка</b>\n"
            "      <b>└ Предпросмотр рассылки</b>\n"
            "\n"
            "<b>Форматирование</b>: 🖌️ {parse_mode}\n"
            "<b>Сообщение для рассылки:</b>\n"
        ).format(
            parse_mode=parse_mode.value
            if parse_mode
            else tm.button.original(),
        )
    )

    state_data["broadcast"]["header_id"] = header_message.message_id
    state_data["broadcast"]["message"] = broadcast_message

    await state.update_data(state_data)

    await message.answer(
        text=broadcast_message,
        reply_markup=create_confirm_keyboard(
            accept_text=tm.button.accept(),
            accept_data=AdminCallbackData(
                action=AdminAction.broadcast_send,
            ),
            decline_text=tm.button.decline(),
            decline_data=AdminCallbackData(
                action=AdminAction.broadcast_get_message,
            ),
        ),
        parse_mode=parse_mode or ParseMode.HTML,
    )


@admin_router.callback_query(
    AdminCallbackData.filter(
        F.action == AdminAction.broadcast_send,
    )
)
async def broadcast_send_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    state_data = await state.get_data()

    if (
        "broadcast" not in state_data
        or "message" not in state_data["broadcast"]
    ):
        await callback.message.edit_text(
            text=tm.message.admin_broadcast_error(),
            reply_markup=create_back_keyboard(
                back_text=tm.button.broadcast(),
                back_data=AdminCallbackData(
                    action=AdminAction.broadcast,
                ),
            ),
        )
        return

    parse_mode = state_data["broadcast"].pop("parse_mode")
    broadcast_message = state_data["broadcast"].pop("message")

    await state.set_data(state_data)

    if not parse_mode:
        parse_mode = ParseMode.HTML

    send_function = await prepare_send_message_function(
        text=broadcast_message,
        parse_mode=parse_mode,
    )

    await broadcast_messages(
        callback=callback,
        send_function=send_function,
    )


@admin_router.callback_query(
    AdminCallbackData.filter(
        F.action == AdminAction.broadcast_send_copy,
    )
)
async def broadcast_send_copy_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    state_data = await state.get_data()
    await state.set_state(None)

    if (
        "broadcast" not in state_data
        or "message_to_copy" not in state_data["broadcast"]
    ):
        await callback.message.edit_text(
            text=tm.message.admin_broadcast_error(),
            reply_markup=create_back_keyboard(
                text=tm.button.broadcast(),
                data=AdminCallbackData(
                    action=AdminAction.broadcast_choose_format,
                ),
            ),
        )
        return

    message_info = state_data["broadcast"].pop("message_to_copy")

    await state.set_state(state_data)

    send_function = await prepare_send_message_copy_function(
        from_chat_id=message_info["from_chat_id"],
        message_id=message_info["message_id"],
    )

    await broadcast_messages(
        callback=callback,
        send_function=send_function,
    )


async def broadcast_messages(
    callback: CallbackQuery,
    send_function: Callable,
):
    bot = callback.bot
    bots_data = db.get_bots()
    bots_data.append({"id": -1, "api_key": bot.token})

    delay = 1 / config.BROADCAST_MESSAGES_PER_SECOND

    broadcast_session = AiohttpSession()

    successful_count = 0

    await callback.message.edit_text(
        text="<b>👨‍💻 Панель администратора</b>\n"
        "   <b>└ ✉️ Рассылка</b>\n"
        "\n"
        "Рассылка началась...",
    )

    for bot_data in bots_data:
        bot = Bot(token=bot_data["api_key"], session=broadcast_session)

        try:
            await bot.get_me()
        except TelegramUnauthorizedError:
            logger.warning("Bot %s unauthorized!", bot_data["id"])
            # TODO: make bot inactive.
            continue

        users_tg_ids = db.get_users_tg_ids_by_bot_id(bot_id=bot_data["id"])

        for user_tg_id in users_tg_ids:
            try:
                user_chat = await bot.get_chat(user_tg_id)
                await send_function(
                    bot=bot,
                    user_tg_id=user_tg_id,
                    username=user_chat.username,
                )
                successful_count += 1
            except TelegramForbiddenError:
                logger.warning(
                    "Bot %s forbidden to send message to user %s!",
                    bot_data["id"],
                    user_tg_id,
                )

            await asyncio.sleep(delay)

    await broadcast_session.close()

    await callback.message.answer(
        text=(
            "<b>👨‍💻 Панель администратора</b>\n"
            "   <b>└ ✉️ Рассылка</b>\n"
            "      <b>└ Рассылка завершена</b>\n"
            "\n"
            "Всего отправлено: <b>{count}</b> сообщений(я).\n"
        ).format(count=successful_count),
        reply_markup=create_back_keyboard(
            text=tm.button.admin_panel(),
            data=AdminCallbackData(
                action=AdminAction.admin_menu,
            ),
        ),
    )


async def send_message(
    bot: Bot,
    user_tg_id: int,
    broadcast_message: str,
    parse_mode: ParseMode,
    username: str,
):
    await bot.send_message(
        chat_id=user_tg_id,
        text=broadcast_message.format(
            username=username,
        ),
        parse_mode=parse_mode,
    )


async def prepare_send_message_function(
    text: str,
    parse_mode: ParseMode,
):
    async def inner_func(
        bot: Bot,
        user_tg_id: int,
        username: str,
    ):
        return await send_message(
            bot=bot,
            user_tg_id=user_tg_id,
            broadcast_message=text,
            parse_mode=parse_mode,
            username=username,
        )

    return inner_func


async def send_message_copy(
    bot: Bot,
    user_tg_id: int,
    from_chat_id: int,
    message_id: int,
):
    await bot.copy_message(
        chat_id=user_tg_id,
        from_chat_id=from_chat_id,
        message_id=message_id,
    )


async def prepare_send_message_copy_function(
    from_chat_id: int,
    message_id: int,
):
    async def inner_func(
        bot: Bot,
        user_tg_id: int,
        username: str,
    ):
        return await send_message_copy(
            bot=bot,
            user_tg_id=user_tg_id,
            from_chat_id=from_chat_id,
            message_id=message_id,
        )

    return inner_func
