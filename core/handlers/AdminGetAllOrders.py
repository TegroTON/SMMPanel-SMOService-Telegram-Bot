from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database as db
from core.keyboards import Button
from core.service_provider.order_status import OrderStatus

# Глобальные переменные для вывода всех заказов
MinOrdersList = 0
MaxOrdersList = 12

AdminAllOrders = Router()


class FSMFillFrom(StatesGroup):
    check_id = State()
    check_link = State()
    check_name = State()


@AdminAllOrders.message(F.text == "Список заказов и статусы")
async def MyOrderAdmin(
    message: Message, bot: Bot, SearchId=None, SearchLink=None, SearchName=None
):
    # Получаем список всех заказов
    if SearchId is None and SearchName is None and SearchLink is None:
        OrderList = await db.GetOrders()
    elif SearchLink is not None:
        OrderList = SearchLink
    elif SearchId is not None:
        OrderList = SearchId
    elif SearchName is not None:
        OrderList = SearchName
    text = ""
    print(OrderList)
    # Проверяем что список больше 0
    if len(OrderList) > 0:
        # Проверяем что они не поместятся в одно сообщение
        if len(OrderList) < 13:
            # Перебираем все заказы пользователя и обновляем статусы
            for order in OrderList:
                NameProduct = await db.GetProductName(order[2])
                Status = OrderStatus(order[9])
                # Проверяем все возможные статусы
                text += (
                    f"{Status.name_with_icon_ru} {NameProduct[0]}"
                    f" {order[4]}шт {order[5]}RUB\n"
                )
            await message.answer(
                text, reply_markup=Button.SearchOrdersAdminKeyboard
            )
        # Если заказы не поместятся в одно сообщение
        else:
            # Перебираем по очереди все сообщения
            for a in range(MinOrdersList, MaxOrdersList):
                if a < len(OrderList):
                    NameProduct = await db.GetProductName(OrderList[a][2])
                    Status = OrderStatus(OrderList[a][9])
                    text += (
                        f"{Status.name_with_icon_ru} {NameProduct[0]}"
                        f" {order[4]}шт {order[5]}RUB\n"
                    )
            if MinOrdersList >= 0:
                if MaxOrdersList == 12:
                    await bot.send_message(
                        message.from_user.id,
                        text,
                        reply_markup=Button.OnlyNextOrdersListAdmin,
                    )
                elif len(OrderList) >= MaxOrdersList > 13:
                    await bot.send_message(
                        message.from_user.id,
                        text,
                        reply_markup=Button.NextOrdersListAdmin,
                    )
                else:
                    await bot.send_message(
                        message.from_user.id,
                        text,
                        reply_markup=Button.BackOrdersListAdmin,
                    )
    # В противном случае выводим что не заказов
    else:
        await message.answer("У вас нет заказов")


# Если человек хочет перейти на след слайд
@AdminAllOrders.callback_query(F.data == "NextOrdersListAdmin")
async def NoSubCategory(callback: CallbackQuery, bot: Bot):
    global MinOrdersList, MaxOrdersList
    MinOrdersList += 12
    MaxOrdersList += 12
    await callback.message.delete()
    await MyOrderAdmin(callback, bot)


# Если человек хочет перейти на прошлый слайд
@AdminAllOrders.callback_query(F.data == "BackOrderListAdmin")
async def NoSubCategory(callback: CallbackQuery, bot: Bot):
    global MinOrdersList, MaxOrdersList
    if MinOrdersList > 0 and MaxOrdersList > 0:
        MinOrdersList -= 12
        MaxOrdersList -= 12
    await callback.message.delete()
    await MyOrderAdmin(callback, bot)


@AdminAllOrders.callback_query(F.data == "SearchForId")
async def SearchForId(call: CallbackQuery, state: FSMContext, bot: Bot):
    await call.message.delete()
    await call.message.answer("Введите id заказа")
    await state.set_state(FSMFillFrom.check_id)


@AdminAllOrders.message(StateFilter(FSMFillFrom.check_id))
async def StateAddSubCategory(message: Message, state: FSMContext, bot: Bot):
    await message.delete()
    Id = message.text
    List = await db.GetOrders(None, Id)
    await MyOrderAdmin(message, bot, List)
    await state.clear()


@AdminAllOrders.callback_query(F.data == "SearchForLink")
async def SearchForLink(call: CallbackQuery, state: FSMContext, bot: Bot):
    await call.message.delete()
    await call.message.answer("Введите ссылку используемую в заказе")
    await state.set_state(FSMFillFrom.check_link)


@AdminAllOrders.message(StateFilter(FSMFillFrom.check_link))
async def StateAddSubCategory(message: Message, state: FSMContext, bot: Bot):
    await message.delete()
    Link = message.text
    List = await db.GetOrders(None, None, Link)
    await MyOrderAdmin(message, bot, None, List)
    await state.clear()
