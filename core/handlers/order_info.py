from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

import database as db
from core.callback_factories.my_orders import (
    MyOrdersAction,
    MyOrdersCallbackData,
)
from core.keyboards.my_orders import create_order_info_keyboard
from core.service_provider.order_status import OrderStatus
from core.text_manager import text_manager as tm

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
            text=tm.message.my_orders_not_found(),
        )
        return

    reply_function = message.edit_text if is_callback else message.answer

    await reply_function(
        text=tm.message.order_info().format(
            name=order["name"],
            id=order["id"],
            export_id=order["order_id"]
            or tm.message.order_info_not_exported(),
            status=OrderStatus(order["status"]).name_with_icon_ru,
            url=order["url"],
            quantity=order["quantity"],
            price=order["sum"],
        ),
        reply_markup=create_order_info_keyboard(
            data=callback_data,
            with_pay_button=(
                OrderStatus.PENDING_PAYMENT.value == order["status"]
            ),
        ),
    )
