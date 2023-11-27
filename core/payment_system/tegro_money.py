import hashlib
import logging
from typing import Dict
from urllib.parse import urlencode

import database as db
from core.config import config
from core.keyboards.utils import create_to_wallet_keyboard
from core.text_manager import text_manager as tm
from core.utils.bot import notify_user

from .currencies import Currency
from .tegro_payment_system_constants import TegroPaymentSystem
from .utils import save_paylink

logger = logging.getLogger("TegroMoney")


class TegroMoney:
    api_url: str
    shop_id: str
    secret_key: str
    api_key: str

    def __init__(self):
        self.api_url = config.TEGRO_API_URL
        self.shop_id = config.TEGRO_SHOP_ID
        self.secret_key = config.TEGRO_SECRET_KEY
        self.api_key = config.TEGRO_API_KEY

    def register_paylink(
        self,
        amount: float,
        user_id: int,
        username: str,
        bot_username: str,
        bot_token: str,
        currency: Currency = Currency.RUB,
        payment_system: TegroPaymentSystem = None,
    ) -> str:
        paylink_id = save_paylink(
            user_id=user_id,
            order_id="",
            payment_gateway="Tegro",
            bot_token=bot_token,
            amount=amount,
        )

        order_id = f"{username}-{user_id}-{paylink_id}"

        db.update_paylink_order_id(
            paylink_id=paylink_id,
            order_id=order_id,
        )

        data = {
            "shop_id": self.shop_id,
            "amount": amount,
            "currency": str(currency),
            "order_id": order_id,
        }

        if config.DEBUG:
            data.update({"test": 1})

        sorted_data = sorted(data.items())
        data_string = urlencode(sorted_data)
        sign = hashlib.md5(
            (data_string + self.secret_key).encode()
        ).hexdigest()

        additional_data = {
            "notify_url": f"{config.BOT_URL}/tegro_ipn",
        }

        if payment_system:
            additional_data["payment_system"] = int(payment_system)

        additional_data_string = urlencode(sorted(additional_data.items()))

        tegro_paylink = (
            f"{self.api_url}?"
            f"{data_string}"
            f"{('&' + additional_data_string) if additional_data else ''}"
            "&receipt[items][0][name]=Replenish"
            "&receipt[items][0][count]=1"
            f"&receipt[items][0][price]={amount}"
            f"&sign={sign}"
        )

        return tegro_paylink

    async def check_ipn_request(
        self,
        request_data: Dict[str, str],
    ):
        if request_data["status"] != "1":
            logger.warning(
                "IPN status mismatch! Request_data: %s", request_data
            )
            return

        order_id = request_data["order_id"]
        paylink_data = db.get_paylink_data_by_order_id(order_id=order_id)

        if not paylink_data:
            logger.warning(
                "Paylink data not found! Request_data: %s",
                request_data,
            )
            return

        if paylink_data["status"] != "pending":
            logger.warning(
                "Paylink already paid! Request_data: %s",
                request_data,
            )
            return

        request_sign = request_data.pop("sign")
        sign = hashlib.md5(
            (
                urlencode(sorted(request_data.items())) + self.secret_key
            ).encode()
        ).hexdigest()

        if sign != request_sign:
            logger.warning("IPN sign mismatch! Request_data: %s", request_data)
            return

        if request_data["status"] == "1":
            user_id = paylink_data["user_id"]

            amount = request_data["amount"]

            db.update_user_balance(user_id, amount)
            db.set_paylink_paid(paylink_data["id"], amount)
            await db.Add_History(user_id, amount, "Пополнение - Tegro")

            logger.info(
                "Successful payment! Payment Gateway: %s. Order_id: %s",
                "Tegro.Money",
                order_id,
            )

            await notify_user(
                user_id=user_id,
                bot=paylink_data["bot_id"],
                message=tm.message.wallet_success_payment().format(
                    amount=paylink_data["amount"],
                    gateway_name="Tegro.Money",
                ),
                reply_markup=create_to_wallet_keyboard(),
            )


tegro_money = TegroMoney()
