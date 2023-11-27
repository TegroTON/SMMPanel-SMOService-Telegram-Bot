import logging

from aiocryptopay import AioCryptoPay, Networks
from aiocryptopay.const import PaidButtons
from aiocryptopay.models.update import Update

import database as db
from core.config import config
from core.keyboards.utils import create_to_wallet_keyboard
from core.text_manager import text_manager as tm
from core.utils.bot import notify_user

from .utils import save_paylink

logger = logging.getLogger("CryptoPay")


class CryptoPay:
    network: Networks
    token: str
    crypto_api: AioCryptoPay

    def __init__(self):
        self.network = Networks.TEST_NET if config.DEBUG else Networks.MAIN_NET
        self.token = (
            config.CRYPTO_TOKEN_TEST if config.DEBUG else config.CRYPTO_TOKEN
        )
        self.crypto_api = AioCryptoPay(
            token=self.token,
            network=self.network,
        )

        self.crypto_api.register_pay_handler(self.update_handler)

    @staticmethod
    async def update_handler(update: Update, app) -> None:
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

        await db.UpdateBalance(user_id, amount)
        db.set_paylink_paid(
            paylink_id=paylink_data["id"],
            amount=amount,
        )
        await db.Add_History(user_id, amount, "Пополнение - CryptoBot")

        logger.info(
            "Successful payment! Payment Gateway: %s. Order_id: %s",
            "CryptoPay",
            invoice.invoice_id,
        )

        await notify_user(
            user_id=user_id,
            bot=paylink_data["bot_id"],
            message=tm.message.wallet_success_payment().format(
                amount=amount,
                gateway_name="CryptoPay",
            ),
            reply_markup=create_to_wallet_keyboard(),
        )

    async def register_paylink(
        self,
        amount: float,
        user_id: int,
        bot_username: str,
        bot_token: str,
    ) -> str | None:
        ton_amount = await self.crypto_api.get_amount_by_fiat(
            summ=amount, asset="TON", target="RUB"
        )

        invoice = await self.crypto_api.create_invoice(
            asset="TON",
            amount=ton_amount,
            paid_btn_name=PaidButtons.OPEN_BOT,
            paid_btn_url=f"https://t.me/{bot_username}",
        )

        save_paylink(
            user_id=user_id,
            order_id=invoice.invoice_id,
            payment_gateway="Crypto",
            bot_token=bot_token,
            amount=amount,
        )

        return invoice.pay_url


cryptopay = CryptoPay()
