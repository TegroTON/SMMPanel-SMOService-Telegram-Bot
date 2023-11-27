from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

import database as db
from core.callback_factories.my_orders import (
    MyOrdersAction,
    MyOrdersCallbackData,
)
from core.config import config
from core.handlers.order_info import process_order_info
from core.keyboards.my_orders import (
    create_orders_list_keyboard,
    create_replenish_for_order_keyboard,
)
from core.service_provider.manager import provider_manager
from core.service_provider.order_status import OrderStatus
from core.text_manager import text_manager as tm

my_orders_router = Router(name="my_orders_router")


@my_orders_router.callback_query(
    MyOrdersCallbackData.filter(F.action == MyOrdersAction.VIEW_ORDERS)
)
async def my_orders_callback_handler(
    callback: CallbackQuery,
    callback_data: MyOrdersCallbackData,
    state: FSMContext,
):
    await state.set_state(None)

    filtered_statuses = [
        *(
            [
                OrderStatus.NEW,
                OrderStatus.PENDING_PAYMENT,
                OrderStatus.STARTING,
                OrderStatus.IN_PROGRESS,
            ]
            if callback_data.filter_active
            else []
        ),
        *(
            [
                OrderStatus.COMPLETED,
                OrderStatus.PARTIAL,
            ]
            if callback_data.filter_completed
            else []
        ),
        *(
            [
                OrderStatus.CANCELED,
            ]
            if callback_data.filter_canceled
            else []
        ),
    ]

    orders = db.get_orders_for_pagination(
        user_id=callback.from_user.id,
        limit=config.PAGINATION_CATEGORIES_PER_PAGE,
        page=callback_data.page,
        statuses=filtered_statuses,
    )

    await callback.message.edit_text(
        text=tm.message.my_orders().format(
            pending=OrderStatus.PENDING_PAYMENT.name_with_icon_ru,
            new=OrderStatus.NEW.name_with_icon_ru,
            in_progress=OrderStatus.IN_PROGRESS.name_with_icon_ru,
            partial=OrderStatus.PARTIAL.name_with_icon_ru,
            completed=OrderStatus.COMPLETED.name_with_icon_ru,
            canceled=OrderStatus.CANCELED.name_with_icon_ru,
        ),
        reply_markup=create_orders_list_keyboard(
            data=callback_data,
            orders=orders,
        ),
    )


@my_orders_router.callback_query(
    MyOrdersCallbackData.filter(F.action == MyOrdersAction.TRY_PAY)
)
async def try_pay_for_order_callback_handler(
    callback: CallbackQuery,
    callback_data: MyOrdersCallbackData,
):
    order = db.get_order_by_id(callback_data.order_id)

    if not order:
        await callback.message.answer(
            text=tm.message.my_orders_not_found(),
        )
        return

    if order["status"] != OrderStatus.PENDING_PAYMENT:
        await callback.message.answer(
            text=tm.message.my_orders_already_paid(),
        )
        return

    user_id = callback.from_user.id

    balance = db.get_user_balance(user_id)

    if balance >= order["sum"]:
        await db.WriteOffTheBalance(user_id, order["sum"])
        db.update_order_status(order["id"], OrderStatus.NEW)

        await db.Add_History(
            user_id=user_id,
            sum=-order["sum"],
            type="Оплата заказа",
            order_id=order["id"],
        )

        await provider_manager.activate_order(
            order["id"],
            order["service_provider"],
        )

        await callback.answer(
            text=tm.message.my_orders_successfully_paid(),
            cache_time=10,
        )

        callback_data.action = MyOrdersAction.VIEW_ORDER
        await process_order_info(
            message=callback.message,
            callback_data=callback_data,
            is_callback=True,
        )

        return

    replenish_amount = order["sum"] - balance

    await callback.message.edit_text(
        text=tm.message.my_orders_insufficient_funds().format(
            replenish_amount=replenish_amount
        ),
        reply_markup=create_replenish_for_order_keyboard(
            data=callback_data,
            amount=replenish_amount,
        ),
    )
