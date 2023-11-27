import hashlib

from aiogram import Bot, Router
from aiogram.filters.command import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)

import database as db
from core.callback_factories.cheques import ChequeType
from core.text_manager import text_manager as tm

common_router = Router(name="common_router")


@common_router.message(Command("get_group_id"))
async def get_group_id_handler(
    message: Message,
    bot: Bot,
):
    text = f"Группа: {message.chat.title}\n" f"ID: {str(message.chat.id)}"
    await bot.send_message(message.from_user.id, text)


@common_router.inline_query()
async def inline_check_handler(
    inline_query: InlineQuery,
    bot: Bot,
) -> None:
    try:
        check_number = int(inline_query.query)
    except ValueError:
        return

    check_data = db.get_check_by_check_number(check_number)

    if not check_data:
        return

    check_type = ChequeType(check_data["typecheck"])
    amount = round(check_data["sum"], 2)
    check_link = check_data["url"]

    if check_type == ChequeType.personal:
        title = tm.message.cheque_inline_title_personal()
        description = tm.message.cheque_inline_description_personal().format(
            amount=amount,
        )
    else:
        quantity = check_data["quantity"]
        title = tm.message.cheque_inline_title_multi()
        description = tm.message.cheque_inline_description_multi().format(
            quantity=quantity,
            amount=amount,
        )

    text = f"{title}\n{description}"

    input_content = InputTextMessageContent(
        message_text=text,
        parse_mode="HTML",
    )

    result_id = hashlib.md5(text.encode()).hexdigest()
    item = InlineQueryResultArticle(
        input_message_content=input_content,
        id=result_id,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"Получить {amount} руб", url=f"{check_link}"
                    )
                ]
            ]
        ),
        title=title,
        description=description,
    )

    await bot.answer_inline_query(
        inline_query_id=inline_query.id,
        results=[item],
        cache_time=1,
    )
