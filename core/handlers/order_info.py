from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

import database as db
from core.callback_factories.my_orders import (
    MyOrdersAction,
    MyOrdersCallbackData,
)
from core.keyboards.my_orders import create_order_info_keyboard
from core.service_provider.order_status import OrderStatus

order_info_router = Router(name="order_info_router")


@order_info_router.callback_query(
    MyOrdersCallbackData.filter(F.action == MyOrdersAction.VIEW_ORDER)
)
async def order_info_callback_handler(
    callback: CallbackQuery,
    callback_data: MyOrdersCallbackData,
):
    await process_order_info(
        message=callback.message,
        callback_data=callback_data,
        is_callback=True,
    )


async def process_order_info(
    message: Message,
    callback_data: MyOrdersCallbackData,
    is_callback: bool = False,
):
    order = db.get_order_by_id(callback_data.order_id)

    if not order:
        await message.answer(
            "Заказ не найден!",
        )
        return

    reply_function = message.edit_text if is_callback else message.answer

    await reply_function(
        text=(
            "<b>Информация о заказе:</b>\n"
            f"{order['name']}\n"
            # "{description}\n\n"
            f"ID:         {order['id']}\n"
            f"Export ID:  {order['order_id'] or 'Присваивается после оплаты'}"
            "\n"
            f"Статус:     {OrderStatus(order['status']).name_with_icon_ru}\n"
            f"Ссылка:     {order['url']}\n"
            f"Количество: {order['quantity']}\n"
            f"Стоимость:  {order['sum']}\n"
        ),
        reply_markup=create_order_info_keyboard(
            data=callback_data,
            with_pay_button=(
                OrderStatus.PENDING_PAYMENT.value == order["status"]
            ),
        ),
    )
