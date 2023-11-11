import validators
from aiogram import F, Router
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

    categories = db.get_categories_for_pagination(
        limit=config.PAGINATION_CATEGORIES_PER_PAGE,
        page=callback_data.page,
        services=provider_manager.get_active_services_names(),
    )

    reply_markup = create_choose_category_keyboard(
        categories=categories,
        data=callback_data,
    )

    await callback.message.edit_text(
        text=("🔥 <b>Создание нового заказа!</b>\n    Выберите категорию:"),
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

    subcategories = db.get_subcategories_for_pagination(
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
        text=(
            "🔥 <b>Создание нового заказа!</b>\n"
            f"    Категория: {category_name}\n"
            "    Выберите подкатегорию:"
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
    category_id = (
        callback_data.subcategory_id
        if callback_data.subcategory_id
        else callback_data.category_id
    )

    products = db.get_products_for_pagination(
        limit=config.PAGINATION_CATEGORIES_PER_PAGE,
        page=callback_data.page,
        category_id=category_id,
    )

    if callback_data.subcategory_id:
        (
            category_name,
            subcategory_name,
        ) = db.get_category_and_subcategory_names(
            subcategory_id=category_id,
        )
    else:
        category_name = db.get_category_name(category_id)
        subcategory_name = "- - - - - -"

    await callback.message.edit_text(
        text=(
            "🔥 <b>Создание нового заказа!</b>\n"
            f"    Категория: {category_name}\n"
            f"    Подкатегория: {subcategory_name}\n"
            "    Выберите услугу:"
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

    await state.set_data(callback_data.model_dump())
    await state.set_state(NewOrderState.enter_quantity)

    await callback.message.edit_text(
        text=(
            f"""👴Заказ услуги '{product["name"]}'\n"""
            f"💳 Цена - {product['price']} руб."
            " за одну единицу (Подписчик, лайк, репост)\n"
            "👇 Введите количество для заказа"
            f" от {product['minorder']} до {product['maxorder']}:"
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
):
    data = await state.get_data()
    product = db.get_product_by_id(data["product_id"])

    try:
        quantity = int(message.text)
        if (
            quantity < 1
            or quantity < product["minorder"]
            or quantity > product["maxorder"]
        ):
            raise ValueError
    except ValueError:
        await message.answer(
            text=(
                "Введите целое число в диапазоне "
                f"от {product['minorder']} до {product['maxorder']}"
            ),
        )
        return

    data["quantity"] = quantity

    await state.update_data(data)
    await state.set_state(NewOrderState.enter_url)

    await message.answer(
        text=(
            " 👇 Введите адрес целевой страницы"
            " (ссылка на фото, профиль, видео):"
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
):
    if not validators.url(message.text):
        await message.answer(
            text=(
                "Это не ссылка!"
                " Введите ссылку в формате: https://example.com"
            )
        )
        return

    data = await state.get_data()
    await state.clear()

    user_id = message.from_user.id
    url = message.text
    data["url"] = url

    product = db.get_product_by_id(data["product_id"])
    total_amount = round(
        data["quantity"] * product["price"], config.BALANCE_PRECISION
    )

    bot_id = db.get_bot_id_by_token(message.bot.token)

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
