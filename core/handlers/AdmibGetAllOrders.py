from aiogram.types import Message, CallbackQuery
from aiogram import F
from core.keyboards import Button
from core.config import config
from aiogram.filters import StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import database as db
import requests
import json
from aiogram import Bot, Router

# Глобальные переменные для вывода всех заказов
MinOrdersList = 0
MaxOrdersList = 12

AdminAllOrders = Router()

class FSMFillFrom(StatesGroup):
    check_id = State()

@AdminAllOrders.message(F.text == 'Список заказов и статусы')
async def MyOrderAdmin(message: Message, bot: Bot, SearchId=None, SearchLink=None, SearchName=None):
    # Получаем список всех заказов
    if SearchId is None and SearchName is None and SearchLink is None:
        OrderList = await db.GetOrders()
    elif SearchLink is not None:
        OrderList = SearchLink
    elif SearchId is not None:
        OrderList = SearchId
    elif SearchName is not None:
        OrderList = SearchName
    print(len(OrderList))
    text = ''
    # Проверяем что список больше 0
    if len(OrderList) > 0:
        # Проверяем что они не поместятся в одно сообщение
        if len(OrderList) < 13:
            # Перебираем все заказы пользователя и обновляем статусы
            for order in OrderList:
                NameProduct = await db.GetProductName(order[2])
                url = 'https://smmpanel.ru/api/v1'
                data = {
                    'key': '6qkjaI5Wb8OsDzrQDagYNPtpbJNdtpGe',
                    'action': 'status',
                    'order': order[8]
                }
                response = requests.post(url, data=data)
                OrderData = json.loads(response.text)
                Status = (OrderData['status'])
                Order_id = (OrderData['order'])
                await db.UpdateOrderStatus(Order_id, Status)
                # Проверяем все возможные статусы
                if Status == 'Pending':
                    text += f'🆕В ожидании {NameProduct} {order[4]}шт {order[5]}RUB\n'
                elif Status == 'In progress':
                    text += f'🔄В работе {NameProduct} {order[4]}шт {order[5]}RUB\n'
                elif Status == 'Processing':
                    text += f'➕Обработка {NameProduct} {order[4]}шт {order[5]}RUB\n'
                elif Status == 'Completed':
                    text += f'☑️Выполнен {NameProduct} {order[4]}шт {order[5]}RUB\n'
                elif Status == 'success':
                    text += f'🆕Новый {NameProduct} {order[4]}шт {order[5]}RUB\n'
                elif Status == 'Partial':
                    text += f'☑️Выполнен частично {NameProduct} {order[4]}шт {order[5]}RUB\n'
                elif Status == 'Canceled':
                    text += f'❌Отменен {NameProduct} {order[4]}шт {order[5]}RUB\n'
            await message.answer(text, reply_markup=Button.SearchOrdersAdminKeyboard)
        # Если заказы не поместятся в одно сообщение
        else:
            # Перебираем по очереди все сообщения
            for a in range(MinOrdersList, MaxOrdersList):
                if a < len(OrderList):
                    NameProduct = 'sdasdasd' #await db.GetProductName(OrderList[a][2])
                    url = 'https://smmpanel.ru/api/v1'
                    data = {
                        'key': '6qkjaI5Wb8OsDzrQDagYNPtpbJNdtpGe',
                        'action': 'status',
                        'order': OrderList[a][8]
                    }
                    response = requests.post(url, data=data)
                    OrderData = json.loads(response.text)
                    Status = (OrderData['status'])
                    Order_id = (OrderData['order'])
                    await db.UpdateOrderStatus(Order_id, Status)
                    if Status == 'Pending':
                        text += f'🆕В ожидании {NameProduct} {OrderList[a][4]}шт {OrderList[a][5]}RUB\n'
                    elif Status == 'In progress':
                        text += f'🔄В работе {NameProduct} {OrderList[a][4]}шт {OrderList[a][5]}RUB\n'
                    elif Status == 'Processing':
                        text += f'➕Обработка {NameProduct} {OrderList[a][4]}шт {OrderList[a][5]}RUB\n'
                    elif Status == 'Completed':
                        text += f'✅Выполнен {NameProduct} {OrderList[a][4]}шт {OrderList[a][5]}RUB\n'
                    elif Status == 'success':
                        text += f'🆕Новый {NameProduct} {OrderList[a][4]}шт {OrderList[a][5]}RUB\n'
                    elif Status == 'Partial':
                        text += f'☑️Выполнен частично {NameProduct} {OrderList[a][4]}шт {OrderList[a][5]}RUB\n'
                    elif Status == 'Canceled':
                        text += f'❌Отменен {NameProduct} {OrderList[a][4]}шт {OrderList[a][5]}RUB\n'
            # Делаем защиту в меньшую и большую сторону
            if MinOrdersList >= 0:
                if MaxOrdersList == 12:
                    await bot.send_message(message.from_user.id, text, reply_markup=Button.OnlyNextOrdersListAdmin)
                elif len(OrderList) >= MaxOrdersList > 13:
                    await bot.send_message(message.from_user.id, text, reply_markup=Button.NextOrdersListAdmin)
                else:
                    await bot.send_message(message.from_user.id, text, reply_markup=Button.BackOrdersListAdmin)
    # В противном случае выводим что не заказов
    else:
        await message.answer('У вас нет заказов')


# Если человек хочет перейти на след слайд
@AdminAllOrders.callback_query(F.data == 'NextOrdersListAdmin')
async def NoSubCategory(callback: CallbackQuery, bot: Bot):
    global MinOrdersList, MaxOrdersList
    MinOrdersList += 12
    MaxOrdersList += 12
    await callback.message.delete()
    await MyOrderAdmin(callback, bot)


# Если человек хочет перейти на прошлый слайд
@AdminAllOrders.callback_query(F.data == 'BackOrderListAdmin')
async def NoSubCategory(callback: CallbackQuery, bot: Bot):
    global MinOrdersList, MaxOrdersList
    if MinOrdersList > 0 and MaxOrdersList > 0:
        MinOrdersList -= 12
        MaxOrdersList -= 12
    await callback.message.delete()
    await MyOrderAdmin(callback, bot)


@AdminAllOrders.callback_query(F.data == 'SearchForId')
async def SearchForId(call: CallbackQuery, state: FSMContext, bot: Bot):
    await call.message.answer('Введите id пользователя')
    await state.set_state(FSMFillFrom.check_id)


@AdminAllOrders.message(StateFilter(FSMFillFrom.check_id))
async def StateAddSubCategory(message: Message, state: FSMContext, bot: Bot):
    await message.delete()
    id = message.text
    await MyOrderAdmin(message, bot, await db.GetOrders(id))
    await state.clear()

