from aiogram import F, Router
from aiogram.types import CallbackQuery

from core.keyboards import TextUser
from core.keyboards.faq import faq_keyboard

FAQRouter = Router()


@FAQRouter.callback_query(F.data == "faq-help")
async def FAQCommand(callback: CallbackQuery):
    await callback.message.edit_text(
        text=(f"{TextUser.FAQText}\n" f"{TextUser.HelpMessage}"),
        reply_markup=faq_keyboard,
    )
