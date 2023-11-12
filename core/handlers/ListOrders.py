from aiogram import Bot, F, Router
from aiogram.filters.command import Command
from aiogram.types import CallbackQuery

import database as db
from core.keyboards import Button

ListOrders = Router()

# Глобальные переменные для вывода всех заказов
MinOrdersList = 0
MaxOrdersList = 12


# Обработка команды мои заказы
@ListOrders.message(Command("myorder"))
async def MyOrderCommand(callback: CallbackQuery, bot: Bot):
    await MyOrder(callback, bot)


@ListOrders.callback_query(F.data == "history_order")
async def MyOrder(callback: CallbackQuery, bot: Bot):
    # Получаем список всех заказов
    OrderList = await db.GetOrders(callback.from_user.id)
    text = ""
    # Проверяем что список больше 0
    if len(OrderList) > 0:
        # Проверяем что они не поместятся в одно сообщение
        if len(OrderList) < 13:
            # Перебираем все заказы пользователя и обновляем статусы
            for order in OrderList:
                NameProduct = await db.GetProductName(order[2])
                Status = order[9]
                # Проверяем все возможные статусы
                print(Status)
                if Status == "Pending":
                    text += f"🆕В ожидании {NameProduct} {order[4]}шт {order[5]}RUB\n"
                elif Status == "In progress" or Status == "Выполняется":
                    text += (
                        f"🔄В работе {NameProduct} {order[4]}шт {order[5]}RUB\n"
                    )
                elif Status == "Processing":
                    text += f"➕Обработка {NameProduct} {order[4]}шт {order[5]}RUB\n"
                elif Status == "Completed" or Status == "Завершен":
                    text += f"☑️Выполнен {NameProduct} {order[4]}шт {order[5]}RUB\n"
                elif Status == "success":
                    text += (
                        f"🆕Новый {NameProduct} {order[4]}шт {order[5]}RUB\n"
                    )
                elif Status == "Partial":
                    text += f"☑️Выполнен частично {NameProduct} {order[4]}шт {order[5]}RUB\n"
                elif Status == "Canceled" or Status == "Отменен":
                    if await db.GetRefundStatus(order[0]) != 1:
                        await db.Refund(order[0])
                        await db.UpdateBalance(callback.from_user.id, order[5])
                        await db.Add_History(
                            callback.from_user.id, order[5], "Отмена заказа"
                        )
                        Referrals = await db.GetReferral(callback.from_user.id)
                        if Referrals is not None:
                            SecondLevelReferral = await db.GetReferral(
                                Referrals
                            )
                            if SecondLevelReferral is not None:
                                ReferralSum = order[5] * 0.04
                                await db.WriteOffTheReferral(
                                    SecondLevelReferral, ReferralSum
                                )
                                await db.WriteOffTheBalance(
                                    SecondLevelReferral, ReferralSum
                                )
                                await db.Add_History(
                                    SecondLevelReferral,
                                    -ReferralSum,
                                    "Отмена заказа реф",
                                )
                            ReferralSum = order[5] * 0.12
                            await db.WriteOffTheReferral(
                                Referrals, ReferralSum
                            )
                            await db.WriteOffTheBalance(Referrals, ReferralSum)
                            await db.Add_History(
                                Referrals, -ReferralSum, "Отмена заказа реф"
                            )
                    text += (
                        f"❌Отменен {NameProduct} {order[4]}шт {order[5]}RUB\n"
                    )
            await callback.message.answer(text)
        # Если заказы не поместятся в одно сообщение
        else:
            # Перебираем по очереди все сообщения
            Status = ""
            for a in range(MinOrdersList, MaxOrdersList):
                if a < len(OrderList):
                    NameProduct = await db.GetProductName(OrderList[a][2])
                    Service = await db.GetServiceCategory(NameProduct[1])
                    Status = OrderList[a][9]
                    if Status == "Pending":
                        text += f"🆕В ожидании {NameProduct[0]} {OrderList[a][4]}шт {OrderList[a][5]}RUB\n"
                    elif Status == "In progress" or Status == "Выполняется":
                        text += f"🔄В работе {NameProduct[0]} {OrderList[a][4]}шт {OrderList[a][5]}RUB\n"
                    elif Status == "Processing":
                        text += f"➕Обработка {NameProduct[0]} {OrderList[a][4]}шт {OrderList[a][5]}RUB\n"
                    elif Status == "Completed" or Status == "Завершен":
                        text += f"✅Выполнен {NameProduct[0]} {OrderList[a][4]}шт {OrderList[a][5]}RUB\n"
                    elif Status == "success":
                        text += f"🆕Новый {NameProduct[0]} {OrderList[a][4]}шт {OrderList[a][5]}RUB\n"
                    elif Status == "Partial":
                        text += f"☑️Выполнен частично {NameProduct[0]} {OrderList[a][4]}шт {OrderList[a][5]}RUB\n"
                    elif Status == "Не оплачен":
                        text += f"❌Не оплачен {NameProduct[0]} {OrderList[a][4]}шт {OrderList[a][5]}RUB\n"
                    elif Status == "Canceled" or Status == "Отменен":
                        if await db.GetRefundStatus(OrderList[a][0]) != 1:
                            await db.Refund(OrderList[a][0])
                            await db.UpdateBalance(
                                callback.from_user.id, OrderList[a][5]
                            )
                            await db.Add_History(
                                callback.from_user.id,
                                OrderList[a][5],
                                "Отмена заказа",
                            )
                            Referrals = await db.GetReferral(
                                callback.from_user.id
                            )
                            if Referrals is not None:
                                SecondLevelReferral = await db.GetReferral(
                                    Referrals
                                )
                                if SecondLevelReferral is not None:
                                    ReferralSum = OrderList[a][5] * 0.04
                                    await db.WriteOffTheReferral(
                                        SecondLevelReferral, ReferralSum
                                    )
                                    await db.WriteOffTheBalance(
                                        SecondLevelReferral, ReferralSum
                                    )
                                    await db.Add_History(
                                        SecondLevelReferral,
                                        -ReferralSum,
                                        "Отмена заказа реф",
                                    )
                                ReferralSum = OrderList[a][5] * 0.12
                                await db.WriteOffTheReferral(
                                    Referrals, ReferralSum
                                )
                                await db.WriteOffTheBalance(
                                    Referrals, ReferralSum
                                )
                                await db.Add_History(
                                    Referrals,
                                    -ReferralSum,
                                    "Отмена заказа реф",
                                )
                        text += f"❌Отменен {NameProduct[0]} {OrderList[a][4]}шт {OrderList[a][5]}RUB\n"
            # Делаем защиту в меньшую и большую сторону
            if MinOrdersList >= 0:
                if MaxOrdersList < 13:
                    await bot.send_message(
                        callback.from_user.id,
                        text,
                        reply_markup=Button.OnlyNextOrdersList,
                    )
                elif len(OrderList) > MaxOrdersList > 12:
                    await bot.send_message(
                        callback.from_user.id,
                        text,
                        reply_markup=Button.NextOrdersList,
                    )
                else:
                    await bot.send_message(
                        callback.from_user.id,
                        text,
                        reply_markup=Button.BackOrdersList,
                    )
    # В противном случае выводим что не заказов
    else:
        await callback.message.answer("У вас нет заказов")


# Если человек хочет перейти на след слайд
@ListOrders.callback_query(F.data == "NextOrdersList")
async def NoSubCategory(callback: CallbackQuery, bot: Bot):
    global MinOrdersList, MaxOrdersList
    MinOrdersList += 12
    MaxOrdersList += 12
    await callback.message.delete()
    await MyOrder(callback, bot)


# Если человек хочет перейти на прошлый слайд
@ListOrders.callback_query(F.data == "BackOrderList")
async def NoSubCategory(callback: CallbackQuery, bot: Bot):
    global MinOrdersList, MaxOrdersList
    MinOrdersList -= 12
    MaxOrdersList -= 12
    await callback.message.delete()
    await MyOrder(callback, bot)
