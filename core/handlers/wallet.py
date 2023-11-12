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
    choose_replenish_amount_keyboard,
    create_pay_keyboard,
    history_keyboard,
    wallet_keyboard,
)
from core.payment_system.cryptopay import register_crypto_paylink
from core.payment_system.tegro_money import register_tegro_paylink
from core.payment_system.tegro_payment_system_constants import (
    TegroPaymentSystem,
)

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
        (await db.GetBalance(callback.from_user.id))[0],
        config.BALANCE_PRECISION,
    )

    text = (
        f"Ваш баланс: {balance} руб.\n"
        "💳 Выберите действие или введите сумму пополнения."
    )

    await state.set_state(WalletState.get_amount)

    if (
        callback.data == "wallet"
        or callback_data
        and callback_data.action == WalletAction.choose_action
    ):
        await callback.message.edit_text(
            text,
            reply_markup=wallet_keyboard,
        )
        return

    await callback.message.answer(
        text,
        reply_markup=wallet_keyboard,
    )


@balance_router.callback_query(
    WalletCallbackData.filter(F.action == WalletAction.replenish),
)
async def replenish_balance_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.message.edit_text(
        "💳 Выберите или введите сумму для пополнения:",
        reply_markup=choose_replenish_amount_keyboard,
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
        bot_token=callback.bot.token,
    )


@balance_router.message(WalletState.get_amount)
async def get_amount_handler(
    message: Message,
    state: FSMContext,
    bot: Bot,
):
    try:
        amount = float(message.text)
        if amount <= config.MIN_REPLENISH_AMOUNT:
            raise ValueError
    except ValueError:
        await message.answer(
            "Минимальная сумма пополнения - {config.MIN_REPLENISH_AMOUNT} руб!"
        )
        return

    await process_get_amount(
        message=message,
        state=state,
        user_id=message.from_user.id,
        username=message.from_user.username,
        amount=amount,
        bot_token=bot.token,
    )


async def process_get_amount(
    message: Message,
    state: FSMContext,
    user_id: int,
    username: str,
    amount: float,
    bot_token: str,
):
    tegro_paylink_card = register_tegro_paylink(
        amount=amount,
        user_id=user_id,
        username=username,
        bot_token=bot_token,
    )

    tegro_paylink_usdt = register_tegro_paylink(
        amount=amount,
        user_id=user_id,
        username=username,
        bot_token=bot_token,
        payment_system=TegroPaymentSystem.TEGRO_PAY,
    )

    crypto_paylink = await register_crypto_paylink(
        amount=amount,
        user_id=user_id,
        bot_token=bot_token,
    )

    await message.answer(
        text=(f"Сумма пополнения: {amount} руб.\n" "Выберите способ оплаты"),
        reply_markup=create_pay_keyboard(
            [
                ("💳Банковской картой", tegro_paylink_card),
                ("💰USDT (Tegro Pay)", tegro_paylink_usdt),
                ("💎Crypto Bot", crypto_paylink),
            ],
        ),
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
    TextAnswer = ""
    date = ""
    Id = 0
    if Datas:
        for data in Datas:
            if data[0] > Id:
                Id = data[0]
                date = data[4]
                month = data[4].split("-")
                TextAnswer = f"<b>• {month[2]}.{month[1]}.{month[0]}</b>\n"
        for data in Datas:
            if data[4] == date:
                Time = data[5].split(":")
                if data[2] > 0:
                    TextAnswer += (
                        f"<i>{Time[0]}:{Time[1]} {data[3]}"
                        f" +{data[2]} рублей</i>\n"
                    )
                else:
                    TextAnswer += (
                        f"<i>{Time[0]}:{Time[1]} {data[3]}"
                        f" {data[2]} рублей</i>\n"
                    )
        await callback.message.edit_text(
            TextAnswer,
            reply_markup=history_keyboard,
        )
    else:
        TextAnswer = "У вас нет операций по счету"
        await callback.answer(TextAnswer)


@balance_router.callback_query(
    WalletCallbackData.filter(F.action == WalletAction.history_document),
)
async def balance_history_document_handler(
    callback: CallbackQuery,
    state: FSMContext,
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
