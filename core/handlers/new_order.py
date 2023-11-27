import validators
from aiogram import Bot, F, Router
from aiogram.filters import StateFilter, or_f
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database as db
from core.callback_factories.my_orders import (
    MyOrdersAction,
    MyOrdersCallbackData,
)
from core.callback_factories.new_order import (
    NewOrderAction,
    NewOrderCallbackData,
)
from core.config import config
from core.handlers.order_info import process_order_info
from core.keyboards.new_order import (
    create_choose_category_keyboard,
    create_choose_product_keyboard,
    create_choose_subcategory_keyboard,
)
from core.keyboards.utils import create_back_keyboard
from core.service_provider.manager import provider_manager
from core.text_manager import text_manager as tm
from core.utils.bot import get_bot_id_by_token

order_router = Router(name="order_router")


class NewOrderState(StatesGroup):
    enter_quantity = State()
    enter_url = State()


@order_router.callback_query(
    or_f(
        NewOrderCallbackData.filter(
            F.action == NewOrderAction.CHOOSE_CATEGORY
        ),
        F.data == "new_order",
    ),
)
async def choose_category_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
    callback_data: NewOrderCallbackData | None = None,
):
    await state.clear()

    if not callback_data:
        callback_data = NewOrderCallbackData()

    categories = db.get_active_categories(
        limit=config.PAGINATION_CATEGORIES_PER_PAGE,
        page=callback_data.page,
        services=provider_manager.get_active_services_names(),
    )

    reply_markup = create_choose_category_keyboard(
        categories=categories,
        data=callback_data,
    )

    await callback.message.edit_text(
        text=tm.message.new_order_choose_category(),
        reply_markup=reply_markup,
    )


@order_router.callback_query(
    NewOrderCallbackData.filter(F.action == NewOrderAction.CHOOSE_SUBCATEGORY)
)
async def choose_subcategory_callback_handler(
    callback: CallbackQuery,
    callback_data: NewOrderCallbackData,
):
    parent_id = callback_data.category_id

    subcategories = db.get_active_subcategories(
        limit=config.PAGINATION_CATEGORIES_PER_PAGE,
        page=callback_data.page,
        parent_id=parent_id,
        services=provider_manager.get_active_services_names(),
    )

    if not subcategories:
        await choose_product_callback_handler(
            callback=callback,
            callback_data=callback_data.model_copy(
                update={
                    "subcategory_id": None,
                }
            ),
        )
        return

    category_name = db.get_category_name(callback_data.category_id)

    await callback.message.edit_text(
        text=tm.message.new_order_choose_subcategory().format(
            category_name=category_name,
        ),
        reply_markup=create_choose_subcategory_keyboard(
            subcategories=subcategories,
            data=callback_data,
        ),
    )


@order_router.callback_query(
    NewOrderCallbackData.filter(F.action == NewOrderAction.CHOOSE_PRODUCT),
)
async def choose_product_callback_handler(
    callback: CallbackQuery,
    callback_data: NewOrderCallbackData,
):
    if callback_data.subcategory_id:
        category_id = callback_data.subcategory_id
        (
            category_name,
            subcategory_name,
        ) = db.get_category_and_subcategory_names(
            subcategory_id=category_id,
        )
    else:
        category_id = callback_data.category_id
        category_name = db.get_category_name(category_id)
        subcategory_name = "- - - - - -"

    products = db.get_active_products(
        limit=config.PAGINATION_CATEGORIES_PER_PAGE,
        page=callback_data.page,
        category_id=category_id,
        services=provider_manager.get_active_services_names(),
    )

    await callback.message.edit_text(
        text=tm.message.new_order_choose_product().format(
            category_name=category_name,
            subcategory_name=subcategory_name,
        ),
        reply_markup=create_choose_product_keyboard(
            products=products,
            data=callback_data,
        ),
    )


@order_router.callback_query(
    NewOrderCallbackData.filter(F.action == NewOrderAction.ENTER_QUANTITY),
)
async def get_quantity_callback_handler(
    callback: CallbackQuery,
    callback_data: NewOrderCallbackData,
    state: FSMContext,
):
    product = db.get_product_by_id(callback_data.product_id)

    if callback_data.subcategory_id:
        category_id = callback_data.subcategory_id
        (
            category_name,
            subcategory_name,
        ) = db.get_category_and_subcategory_names(
            subcategory_id=category_id,
        )
    else:
        category_id = callback_data.category_id
        category_name = db.get_category_name(category_id)
        subcategory_name = "- - - - - -"

    await state.set_data(callback_data.model_dump())
    await state.set_state(NewOrderState.enter_quantity)

    await callback.message.edit_text(
        text=tm.message.new_order_enter_amount().format(
            category_name=category_name,
            subcategory_name=subcategory_name,
            title=product["name"],
            price=product["price"],
            min_quantity=product["minorder"],
            max_quantity=product["maxorder"],
        ),
        reply_markup=create_back_keyboard(
            data=callback_data.model_copy(
                update={
                    "action": NewOrderAction.CHOOSE_PRODUCT,
                }
            )
        ),
    )


@order_router.message(
    StateFilter(NewOrderState.enter_quantity),
)
async def enter_quantity_handler(
    message: Message,
    state: FSMContext,
    bot: Bot,
):
    data = await state.get_data()
    product = db.get_product_by_id(data["product_id"])

    if "mistake_message_id" in data and data["mistake_message_id"]:
        await bot.delete_message(
            chat_id=message.chat.id,
            message_id=data.pop("mistake_message_id"),
        )

    if data["subcategory_id"]:
        category_id = data["subcategory_id"]
        (
            category_name,
            subcategory_name,
        ) = db.get_category_and_subcategory_names(
            subcategory_id=category_id,
        )
    else:
        category_id = data["category_id"]
        category_name = db.get_category_name(category_id)
        subcategory_name = "- - - - - -"

    try:
        quantity = int(message.text)
        if (
            quantity < 1
            or quantity < product["minorder"]
            or quantity > product["maxorder"]
        ):
            raise ValueError
    except ValueError:
        mistake_message = await message.answer(
            text=tm.message.new_order_wrong_quantity().format(
                min_quantity=product["minorder"],
                max_quantity=product["maxorder"],
            ),
        )
        await state.update_data(
            {
                "mistake_message_id": mistake_message.message_id,
            }
        )
        await message.delete()
        return

    data["quantity"] = quantity

    await state.set_data(data)
    await state.set_state(NewOrderState.enter_url)

    await message.answer(
        text=tm.message.new_order_enter_url().format(
            category_name=category_name,
            subcategory_name=subcategory_name,
            title=product["name"],
            price=product["price"],
            quantity=quantity,
        ),
        reply_markup=create_back_keyboard(
            data=NewOrderCallbackData(
                **{
                    **data,
                    "action": NewOrderAction.ENTER_QUANTITY,
                },
            ),
        ),
    )


@order_router.message(
    StateFilter(NewOrderState.enter_url),
)
async def enter_link_handler(
    message: Message,
    state: FSMContext,
    bot: Bot,
):
    data = await state.get_data()

    if "mistake_message_id" in data and data["mistake_message_id"]:
        await bot.delete_message(
            chat_id=message.chat.id,
            message_id=data.pop("mistake_message_id"),
        )

    if not validators.url(message.text):
        mistake_message = await message.answer(
            text=tm.message.new_order_wrong_link(),
        )
        await state.update_data(
            {
                "mistake_message_id": mistake_message.message_id,
            }
        )
        await message.delete()
        return

    await state.clear()

    user_id = message.from_user.id
    url = message.text
    data["url"] = url

    product = db.get_product_by_id(data["product_id"])
    total_amount = round(
        data["quantity"] * product["price"], config.PRODUCT_PRICE_PRECISION
    )

    bot_id = get_bot_id_by_token(message.bot.token)

    internal_order_id = db.add_order(
        user_id=user_id,
        product_id=data["product_id"],
        service_id=product["service_id"],
        quantity=data["quantity"],
        total_amount=total_amount,
        url=url,
        bot_id=bot_id,
    )

    await process_order_info(
        message=message,
        callback_data=MyOrdersCallbackData(
            action=MyOrdersAction.VIEW_ORDER,
            order_id=internal_order_id,
        ),
    )
    return
