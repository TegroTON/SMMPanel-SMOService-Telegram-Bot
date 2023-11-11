from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from core.config import config
from core.keyboards import Button

AdminRouter = Router()


@AdminRouter.callback_query(
    F.data == "admin",
)
async def admin_panel_callback_handler(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "Вы попали в админ-панель",
        reply_markup=Button.ReplyAdminPanelKeyboard,
    )


# Обрабатываем нажатие на кнопку Админ-Панель
@AdminRouter.message(F.text == "Админ-панель")
async def CreateAnOrder(
    message: Message,
    state: FSMContext,
):
    await state.clear()
    if message.from_user.id == config.ADMIN_ID:
        await message.answer(
            "Выберите действие", reply_markup=Button.ReplyAdminPanelKeyboard
        )
    else:
        await message.answer("Я не знаю такой команды")
