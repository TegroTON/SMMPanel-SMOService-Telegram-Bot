from aiogram.filters.callback_data import CallbackData


class PaginationCallbackData(
    CallbackData, prefix="pgntn"
):  # prefix: pagination
    page: int = 1
