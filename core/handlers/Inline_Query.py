from core.config import config
import database as db
import hashlib
from aiogram.types import InputTextMessageContent, InlineQueryResultArticle, InlineQuery
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import main
from aiogram import Bot, Router

QueryRouter = Router()


@QueryRouter.inline_query()
async def InlineQuery(inline_query: InlineQuery, bot: Bot) -> None:
    text = inline_query.query
    data = await db.GetCheckForUser(None, None, text)
    Text = f'🧾<b>Мульти-чек на {data[2]}</b>\n' \
           f'\n' \
           f'<b>Внутри чек:</b> {data[3]} активация(й) по {data[2]}рублей'
    input_content = InputTextMessageContent(message_text=Text, parse_mode="HTML")
    result_id = hashlib.md5(text.encode()).hexdigest()
    AllSum = int(data[2]) * int(data[3])
    Item = InlineQueryResultArticle(
        input_message_content=input_content,
        id=result_id,
        reply_markup=await Keyboard(data[4], data[2]),
        title=f'Мульти-чек на {AllSum}рублей',
        description=f'Одна активация: {data[2]}·{AllSum}·{data[3]}'
    )

    await bot.answer_inline_query(inline_query_id=inline_query.id,
                                         results=[Item],
                                         cache_time=1)


async def Keyboard(link, Sum):
    Button = [
        [
            InlineKeyboardButton(text=f'Получить {Sum} рублей', url=f'{link}')
        ]
    ]
    KeyboardUrl = InlineKeyboardMarkup(inline_keyboard=Button)
    return KeyboardUrl
