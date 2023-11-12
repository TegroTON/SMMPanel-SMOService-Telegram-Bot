import hashlib

from aiogram import Bot, Router
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

import database as db
from core.callback_factories.checks import CheckType

QueryRouter = Router()


@QueryRouter.inline_query()
async def InlineQuery(inline_query: InlineQuery, bot: Bot) -> None:
    try:
        check_number = int(inline_query.query)
    except ValueError:
        return

    check_data = db.get_check_by_check_number(check_number)

    if not check_data:
        return

    check_type = CheckType(check_data["typecheck"])
    amount = round(check_data["sum"], 2)
    check_link = check_data["url"]

    if check_type == CheckType.personal:
        title = "🧾<b>Персональный чек</b>"
        description = f"Внутри {amount} руб"
        text = f"🧾<b>Персональный чек</b>\n\n" f"Внутри {amount} руб"
    else:
        quantity = check_data["quantity"]
        title = "🧾<b>Мульти-чек</b>"
        description = f"Внутри {quantity} активация(й) по {amount} руб"
        text = (
            "🧾<b>Мульти-чек</b>\n\n"
            f"Внутри {quantity} активация(й) по {amount} руб"
        )

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
