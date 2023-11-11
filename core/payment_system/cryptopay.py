from aiocryptopay import AioCryptoPay, Networks
from aiocryptopay.models.update import Update

import database as db
from core.config import config
from core.keyboards import Button
from core.utils.bot import get_bot_by_id

from .utils import save_paylink

network = Networks.TEST_NET if config.DEBUG else Networks.MAIN_NET
token = config.CRYPTO_TOKEN_TEST if config.DEBUG else config.CRYPTO_TOKEN
crypto = AioCryptoPay(
    token=token,
    network=network,
)


async def register_crypto_paylink(
    amount: float,
    user_id: int,
    bot_token: str,
) -> str | None:
    ton_amount = await crypto.get_amount_by_fiat(
        summ=amount, asset="TON", target="RUB"
    )
    invoice = await crypto.create_invoice(asset="TON", amount=ton_amount)

    save_paylink(
        user_id=user_id,
        order_id=invoice.invoice_id,
        payment_gateway="Crypto",
        bot_token=bot_token,
        amount=amount,
    )

    return invoice.pay_url


@crypto.pay_handler()
async def invoice_paid(update: Update, app) -> None:
    invoice = update.payload

    paylink_data = db.get_paylink_data_by_order_id(invoice.invoice_id)

    if (
        not paylink_data
        or paylink_data["status"] != "pending"
        or invoice.status != "paid"
    ):
        return

    user_id = paylink_data["user_id"]
    amount = paylink_data["amount"]

    bot = get_bot_by_id(paylink_data["bot_id"])

    await db.UpdateBalance(user_id, amount)
    await db.Add_History(user_id, amount, "Пополнение - CryptoBot")

    await bot.send_message(
        chat_id=user_id,
        text=(
            "Оплата прошла успешно.\n"
            "Сервис: CryptoBot\n"
            f"Сумма: {amount} руб."
        ),
        reply_markup=Button.ReplyStartKeyboard,
    )
    await bot.session.close()
