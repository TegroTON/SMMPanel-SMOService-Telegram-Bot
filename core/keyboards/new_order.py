from typing import Any, Dict, List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.callback_factories.my_orders import (
    MyOrdersAction,
    MyOrdersCallbackData,
)
from core.callback_factories.new_order import (
    NewOrderAction,
    NewOrderCallbackData,
)
from core.config import config
from core.keyboards.utils import create_pagination_buttons
from core.text_manager import text_manager as tm

from .utils import create_to_main_menu_button


def create_choose_category_keyboard(
    categories: List[Dict[str, Any]],
    data: NewOrderCallbackData,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    has_next_page = False
    if len(categories) > config.PAGINATION_CATEGORIES_PER_PAGE:
        categories = categories[: config.PAGINATION_CATEGORIES_PER_PAGE]
        has_next_page = True

    data.action = NewOrderAction.CHOOSE_SUBCATEGORY
    for category in categories:
        builder.add(
            InlineKeyboardButton(
                text=category["name"],
                callback_data=data.model_copy(
                    update={
                        "category_id": category["id"],
                        "page": 1,
                    }
                ).pack(),
            )
        )

    builder.adjust(2)

    data.action = NewOrderAction.CHOOSE_CATEGORY
    pagination_buttons = create_pagination_buttons(data, has_next_page)

    builder.row(*pagination_buttons)

    builder.row(
        InlineKeyboardButton(
            text=tm.button.back(),
            callback_data="main_menu",
        ),
    )

    return builder.as_markup()


def create_choose_subcategory_keyboard(
    subcategories: List[Dict[str, Any]],
    data: NewOrderCallbackData,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    has_next_page = False
    if len(subcategories) > config.PAGINATION_CATEGORIES_PER_PAGE:
        subcategories = subcategories[: config.PAGINATION_CATEGORIES_PER_PAGE]
        has_next_page = True

    data.action = NewOrderAction.CHOOSE_PRODUCT
    for subcategory in subcategories:
        builder.row(
            InlineKeyboardButton(
                text=subcategory["name"],
                callback_data=data.model_copy(
                    update={
                        "subcategory_id": subcategory["id"],
                        "page": 1,
                    }
                ).pack(),
            )
        )

    data.action = NewOrderAction.CHOOSE_SUBCATEGORY
    pagination_buttons = create_pagination_buttons(data, has_next_page)

    builder.row(*pagination_buttons)

    builder.row(
        InlineKeyboardButton(
            text=tm.button.back(),
            callback_data=data.model_copy(
                update={"action": NewOrderAction.CHOOSE_CATEGORY},
            ).pack(),
        )
    )

    return builder.as_markup()


def create_choose_product_keyboard(
    products: List[Dict[str, Any]],
    data: NewOrderCallbackData,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    has_next_page = False
    if len(products) > config.PAGINATION_CATEGORIES_PER_PAGE:
        products = products[: config.PAGINATION_CATEGORIES_PER_PAGE]
        has_next_page = True

    data.action = NewOrderAction.ENTER_QUANTITY
    for product in products:
        builder.row(
            InlineKeyboardButton(
                text=product["name"],
                callback_data=data.model_copy(
                    update={
                        "product_id": product["id"],
                        "page": 1,
                    }
                ).pack(),
            )
        )

    data.action = NewOrderAction.CHOOSE_PRODUCT
    pagination_buttons = create_pagination_buttons(data, has_next_page)

    builder.row(*pagination_buttons)

    prev_action = (
        NewOrderAction.CHOOSE_SUBCATEGORY
        if data.subcategory_id
        else NewOrderAction.CHOOSE_CATEGORY
    )
    builder.row(
        InlineKeyboardButton(
            text=tm.button.back(),
            callback_data=data.model_copy(
                update={"action": prev_action},
            ).pack(),
        )
    )

    return builder.as_markup()


def create_order_created_keyboard(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=tm.button.to_order(),
            callback_data=MyOrdersCallbackData(
                action=MyOrdersAction.VIEW_ORDER,
                order_id=order_id,
            ).pack(),
        )
    )

    builder.row(
        create_to_main_menu_button(),
    )

    return builder.as_markup()
