import os

from aiogram import Bot, F, Router
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.types.input_file import FSInputFile

import database as db
from core.callback_factories.wallet import WalletAction, WalletCallbackData
from core.config import config
from core.keyboards.wallet import (
    create_choose_replenish_amount_keyboard,
    create_history_keyboard,
    create_pay_keyboard,
    create_wallet_keyboard,
)
from core.payment_system.cloudpayments import cloudpayments
from core.payment_system.cryptopay import cryptopay
from core.payment_system.tegro_money import tegro_money
from core.payment_system.tegro_payment_system_constants import (
    TegroPaymentSystem,
)

# from core.payment_system.ton_wallet import register_ton_wallet_paylink
from core.text_manager import text_manager as tm

balance_router = Router()


class WalletState(StatesGroup):
    get_amount = State()


@balance_router.callback_query(
    or_f(
        F.data == "wallet",
        WalletCallbackData.filter(F.action == WalletAction.choose_action),
    ),
)
async def wallet_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
    callback_data: WalletCallbackData | None = None,
):
    await state.clear()

    balance = round(
        db.get_user_balance(callback.from_user.id),
        config.BALANCE_PRECISION,
    )

    text = tm.message.wallet().format(balance=balance)

    await state.set_state(WalletState.get_amount)

    if (
        callback.data == "wallet"
        or callback_data
        and callback_data.action == WalletAction.choose_action
    ):
        await callback.message.edit_text(
            text,
            reply_markup=create_wallet_keyboard(),
        )
        return

    await callback.message.answer(
        text,
        reply_markup=create_wallet_keyboard(),
    )


@balance_router.callback_query(
    WalletCallbackData.filter(F.action == WalletAction.replenish),
)
async def replenish_balance_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.message.edit_text(
        text=tm.message.wallet_get_sum(),
        reply_markup=create_choose_replenish_amount_keyboard(),
    )
    await state.set_state(WalletState.get_amount)


@balance_router.callback_query(
    WalletCallbackData.filter(F.action == WalletAction.get_amount),
)
async def get_amount_callback_handler(
    callback: CallbackQuery,
    callback_data: WalletCallbackData,
    state: FSMContext,
):
    await process_get_amount(
        message=callback.message,
        state=state,
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        amount=callback_data.amount,
        bot=callback.bot,
    )


@balance_router.message(WalletState.get_amount)
async def get_amount_handler(
    message: Message,
    state: FSMContext,
):
    try:
        amount = float(message.text)
        if amount < config.MIN_REPLENISH_AMOUNT:
            raise ValueError
    except ValueError:
        await message.answer(
            tm.message.wallet_replenish_min_sum().format(
                min_sum=config.MIN_REPLENISH_AMOUNT
            )
        )
        return

    await process_get_amount(
        message=message,
        state=state,
        user_id=message.from_user.id,
        username=message.from_user.username,
        amount=amount,
        bot=message.bot,
    )


async def process_get_amount(
    message: Message,
    state: FSMContext,
    user_id: int,
    username: str,
    amount: float,
    bot: Bot,
):
    bot_username = (await bot.get_me()).username

    paylinks = {}

    paylinks["💳 Банковской картой"] = tegro_money.register_paylink(
        amount=amount,
        user_id=user_id,
        username=username,
        bot_username=bot_username,
        bot_token=bot.token,
    )

    paylinks["💲 USDT"] = tegro_money.register_paylink(
        amount=amount,
        user_id=user_id,
        username=username,
        bot_username=bot_username,
        bot_token=bot.token,
        payment_system=TegroPaymentSystem.TETHER_USDT_BNB_SMART_CHAIN,
    )

    if user_id == config.ADMIN_ID:
        paylinks["📱 CloudPayments"] = await cloudpayments.register_paylink(
            amount=amount,
            user_id=user_id,
            bot_username=bot_username,
            bot_token=bot.token,
            username=username,
        )

    paylinks["💎 Crypto Bot"] = await cryptopay.register_paylink(
        amount=amount,
        user_id=user_id,
        bot_username=bot_username,
        bot_token=bot.token,
    )

    # paylinks["👛 Wallet Pay"] = await register_ton_wallet_paylink(
    #     amount=amount,
    #     user_id=user_id,
    #     bot_username=bot_username,
    # )

    await message.answer(
        text=tm.message.wallet_replenish_choose_method().format(amount=amount),
        reply_markup=create_pay_keyboard(paylinks=paylinks),
    )

    await state.clear()


@balance_router.callback_query(
    WalletCallbackData.filter(F.action == WalletAction.history),
)
async def balance_history_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await state.clear()

    Datas = await db.Get_History(callback.from_user.id)
    operations = ""
    date = ""
    Id = 0
    if Datas:
        for data in Datas:
            if data[0] > Id:
                Id = data[0]
                date = data[4]
                month = data[4].split("-")
                operations = f"<b>• {month[2]}.{month[1]}.{month[0]}</b>\n"
        for data in Datas:
            if data[4] == date:
                Time = data[5].split(":")
                if data[2] > 0:
                    operations += (
                        f"<i>{Time[0]}:{Time[1]} {data[3]}"
                        f" +{data[2]} рублей</i>\n"
                    )
                else:
                    operations += (
                        f"<i>{Time[0]}:{Time[1]} {data[3]}"
                        f" {data[2]} рублей</i>\n"
                    )
        await callback.message.edit_text(
            text=tm.message.wallet_history().format(operations=operations),
            reply_markup=create_history_keyboard(),
        )
    else:
        await callback.answer(tm.message.wallet_no_history())


@balance_router.callback_query(
    WalletCallbackData.filter(F.action == WalletAction.history_document),
)
async def balance_history_document_handler(
    callback: CallbackQuery,
    bot: Bot,
):
    Datas = await db.Get_History(callback.from_user.id)
    file = open(f"отчет_{callback.from_user.id}.txt", "w+")
    date = ""
    for data in Datas:
        if date != data[4]:
            date = data[4]
            day = date.split("-")[2]
            month = date.split("-")[1]
            year = date.split("-")[0]
            file.write(f"{day}.{month}.{year}\n")
        hour = data[5].split(":")[0]
        minute = data[5].split(":")[1]
        file.write(f"{hour}:{minute} {data[3]} {data[2]} рублей\n")
    file.close()
    document = FSInputFile(f"отчет_{callback.from_user.id}.txt")
    await bot.send_document(callback.from_user.id, document)

    os.remove(file.name)
