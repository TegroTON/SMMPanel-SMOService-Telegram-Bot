import logging
import hashlib
from typing import Dict
from urllib.parse import urlencode

import database as db
from core.config import config
from core.utils.bot import get_bot_by_id

from .utils import save_paylink
from .tegro_payment_system_constants import TegroPaymentSystem
from .currencies import Currency

logger = logging.getLogger(__name__)


def register_tegro_paylink(
    amount: float,
    user_id: int,
    username: str,
    bot_token: str,
    currency: Currency = Currency.RUB,
    payment_system: TegroPaymentSystem = None,
) -> str | None:
    paylink_id = save_paylink(
        user_id=user_id,
        order_id="",
        payment_gateway="Tegro",
        bot_token=bot_token,
        amount=amount,
    )

    order_id = f"{username}:{user_id}:{paylink_id}"

    db.update_paylink_order_id(
        paylink_id=paylink_id,
        order_id=order_id,
    )

    data = {
        "shop_id": config.TEGRO_SHOP_ID,
        "amount": amount,
        "currency": str(currency),
        "order_id": order_id,
    }

    if config.DEBUG:
        data.update({"test": 1})

    sorted_data = sorted(data.items())
    data_string = urlencode(sorted_data)
    sign = hashlib.md5(
        (data_string + config.TEGRO_SECRET_KEY).encode()
    ).hexdigest()

    additional_data = {}

    if payment_system:
        additional_data["payment_system"] = int(payment_system)

    additional_data_string = urlencode(sorted(additional_data.items()))

    tegro_paylink = (
        "https://tegro.money/pay/?"
        f"{data_string}"
        f"{('&' + additional_data_string) if additional_data else ''}"
        "&receipt[items][0][name]=Replenish"
        "&receipt[items][0][count]=1"
        f"&receipt[items][0][price]={amount}"
        f"&sign={sign}"
    )

    return tegro_paylink


async def tegro_success(response_data: Dict[str, str]):
    order_id = response_data["order_id"]
    paylink_data = db.get_paylink_data_by_order_id(order_id=order_id)

    response_sign = response_data.pop("sign")
    sign = hashlib.md5(
        (
            urlencode(sorted(response_data.items())) + config.TEGRO_SECRET_KEY
        ).encode()
    ).hexdigest()

    if (
        sign != response_sign
        or response_data["status"] != "1"
        or not paylink_data
        or paylink_data["status"] != "pending"
    ):
        return

    if response_data["status"] == "1":
        user_id = paylink_data["user_id"]

        db.update_user_balance(user_id, response_data["amount"])
        db.set_paylink_paid(paylink_data["id"])
        await db.Add_History(
            user_id, response_data["amount"], "Пополнение - Tegro"
        )

        bot = get_bot_by_id(paylink_data["bot_id"])

        await bot.send_message(
            chat_id=user_id,
            text=(
                "Оплата прошла успешно.\n"
                "Сервис: Tegro.pay\n"
                "Сумма: {} руб.".format(paylink_data["amount"])
            ),
        )
        await bot.session.close()


async def tegro_fail(request):
    logger.warning("Tegro payment failed")
