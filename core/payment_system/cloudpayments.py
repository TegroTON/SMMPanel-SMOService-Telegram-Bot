import base64
import hmac
import logging
import time
from urllib.parse import parse_qs
from core.keyboards.utils import create_to_wallet_keyboard
from core.utils.bot import notify_user

import database as db
from core.config import config
from core.payment_system.utils import save_paylink
from core.utils.http import http_request
from core.text_manager import text_manager as tm

from .currencies import Currency

logger = logging.getLogger("CloudPayments")


class CloudPayments:
    api_url: str = config.CLOUDPAYMENTS_API_URL
    public_id: str
    api_key: str

    def __init__(self) -> None:
        self.public_id = config.CLOUDPAYMENTS_PUBLIC_ID
        self.api_key = config.CLOUDPAYMENTS_SECRET_KEY

    async def register_paylink(
        self,
        amount: int,
        username: str,
        bot_username: str,
        user_id: int,
        bot_token: str,
    ) -> str:
        paylink_id = save_paylink(
            user_id=user_id,
            order_id="",
            payment_gateway="CloudPayments",
            bot_token=bot_token,
            amount=amount,
        )

        paylink_order_id = f"{username}-{user_id}-{paylink_id}"

        db.update_paylink_order_id(
            paylink_id=paylink_id,
            order_id=paylink_order_id,
        )

        headers = {
            "X-Request-ID": f"{self.public_id}-{time.time_ns()}",
            "Content-Type": "application/json",
        }

        data = {
            "Amount": round(amount, 2),
            "Currency": Currency.RUB,
            "Description": "Пополнение баланса.",
            "SuccessRedirectUrl": f"https://t.me/{bot_username}",
            "FailRedirectUrl": f"https://t.me/{bot_username}",
            "InvoiceId": paylink_order_id,
            "AccountId": user_id,
        }

        response = await http_request(
            url=f"{self.api_url}/orders/create",
            headers=headers,
            json_data=data,
            user=self.public_id,
            password=self.api_key,
        )

        if not response:
            return ""

        response_data = response.json()

        if (
            not response_data
            or not {"Model", "Success"}.issubset(response_data)
            or not {"Id", "Url", "InternalId"}.issubset(response_data["Model"])
        ):
            return ""

        return response_data["Model"]["Url"]

    async def check_ipn(
        self,
        data: bytes,
        headers: dict,
    ) -> int:
        request_data = {
            key: value[0]
            for key, value in parse_qs(str(data, "utf-8")).items()
        }

        logger.info(
            "Checking ipn.\n Headers: %s\n Data: %s", headers, request_data
        )

        signature = base64.b64encode(
            hmac.new(
                cloudpayments.api_key.encode(), data, digestmod="sha256"
            ).digest()
        )

        if str(signature, "utf-8") not in {
            headers.get("Content-HMAC"),
            headers.get("Content-Hmac"),
        }:
            logger.warning("IPN sign mismatch!")
            return 999

        order_id = request_data["InvoiceId"]

        paylink = db.get_paylink_data_by_order_id(order_id=order_id)

        if not paylink:
            logger.warning("Paylink data not found!")
            return 999

        if paylink["status"] != "pending":
            logger.warning("Paylink already paid!")
            return 999

        if paylink["amount"] != float(request_data["Amount"]):
            logger.warning("Paylink amount mismatch!")
            return 999

        if paylink["user_id"] != int(request_data["AccountId"]):
            logger.warning("Paylink user_id mismatch!")
            return 999

        db.set_paylink_paid(
            paylink_id=paylink["id"],
            amount=request_data["Amount"],
        )

        if not config.DEBUG and request_data["TestMode"] == "1":
            logger.info("Test payments success!")
            await notify_user(
                user_id=paylink["user_id"],
                bot=paylink["bot_id"],
                message=f"""{tm.message.wallet_success_payment().format(
                    amount=paylink["amount"],
                    gateway_name="CloudPayments",
                )}\n Это тестовая оплата. Деньги не зачисляются на баланс!""",
                reply_markup=create_to_wallet_keyboard(),
            )
            return 1

        amount = float(request_data["Amount"])

        db.update_user_balance(paylink["user_id"], amount)
        db.set_paylink_paid(paylink["id"], amount)
        await db.Add_History(
            paylink["user_id"], amount, "Пополнение - CloudPayments"
        )

        logger.info(
            "Successful payment! Payment Gateway: %s. Order_id: %s",
            "CloudPayments",
            order_id,
        )

        await notify_user(
            user_id=paylink["user_id"],
            bot=paylink["bot_id"],
            message=tm.message.wallet_success_payment().format(
                amount=paylink["amount"],
                gateway_name="CloudPayments",
            ),
            reply_markup=create_to_wallet_keyboard(),
        )

        return 1


cloudpayments = CloudPayments()
