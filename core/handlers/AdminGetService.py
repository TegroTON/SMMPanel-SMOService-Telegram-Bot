from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from core.config import config
from core.keyboards import Button

from core.service_provider.manager import provider_manager

AdminGetServiceRouter = Router()


@AdminGetServiceRouter.message(F.text == "Выбрать сервис для создания заказа")
async def CreateAnOrder(message: Message):
    await message.answer(
        "Выберите сервис с которого буду браться продукты и делаться заказы(значение по умолчанию Вместе)",
        reply_markup=Button.GetServiceKeyboard,
    )


@AdminGetServiceRouter.callback_query(F.data == "SmoService")
async def CheckPay(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    # TODO: Temporary solution.
    config.Service = "SmoService"
    provider_manager.deactivate_service("SmmPanel")
    provider_manager.activate_service_provider("SmoService")
    await callback.message.answer(
        "Теперь сервис для обработки заказов SmoService"
    )


@AdminGetServiceRouter.callback_query(F.data == "SmmPanelService")
async def CheckPay(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    # TODO: Temporary solution.
    config.Service = "SmmPanel"
    provider_manager.deactivate_service("SmoService")
    provider_manager.activate_service_provider("SmmPanel")
    await callback.message.answer(
        "Теперь сервис для обработки заказов SmmPanel"
    )


@AdminGetServiceRouter.callback_query(F.data == "All_service")
async def CheckPay(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    # TODO: Temporary solution.
    config.Service = "All"
    provider_manager.activate_all_services()
    await callback.message.answer(
        "Теперь работает сразу два сервиса для обработки заказов"
    )
