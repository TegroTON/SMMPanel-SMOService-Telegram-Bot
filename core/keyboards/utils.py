from typing import List

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.callback_factories.pagination import PaginationCallbackData


def create_back_keyboard(
    data: CallbackData,
    text: str | None = None,
) -> InlineKeyboardMarkup:
    if not text:
        text = "Назад"

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=text,
            callback_data=data.pack(),
        )
    )

    return builder.as_markup()


def create_pagination_buttons(
    data: PaginationCallbackData,
    has_next_page: bool = False,
) -> List[InlineKeyboardButton]:
    page = data.page

    buttons = []

    if page > 1:
        buttons.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=data.model_copy(
                    update={"page": page - 1}
                ).pack(),
            )
        )

    if has_next_page:
        buttons.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=data.model_copy(
                    update={"page": page + 1},
                ).pack(),
            )
        )

    return buttons
