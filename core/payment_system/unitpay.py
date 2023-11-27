import hashlib
import logging
from enum import StrEnum
from typing import Any, Dict

from aiogram.enums.parse_mode import ParseMode

import database as db
from core.config import config
from core.keyboards.utils import create_to_wallet_keyboard
from core.payment_system.currencies import Currency
from core.payment_system.utils import save_paylink
from core.text_manager import text_manager as tm
from core.utils.bot import get_bot_by_id
from core.utils.http import http_request

logger = logging.getLogger(__name__)


class UnitPayCheckMethod(StrEnum):
    CHECK = "check"
    PAY = "pay"
    PREAUTH = "preauth"
    ERROR = "error"


class UnitPayRequestMethod(StrEnum):
    INIT_PAYMENT = "initPayment"
    GET_PAYMENT = "getPayment"


class UnitPaymentSystemCode(StrEnum):
    CARD = "card", "Пластиковые карты", "Прием платежей с карт всего мира"
    QIWI = (
        "qiwi",
        "Qiwi",
        "Электронная платежная система, а также сеть терминалов оплаты",
    )
    SBP = (
        "sbp",
        "Система быстрых платежей",
        "Прием платежей с карт с помощью Системы Быстрых Платежей",
    )
    YANDEXPAY = (
        "yandexpay",
        "Yandex Pay",
        "Прием платежей с карт с помощью Yandex Pay",
    )
    APPLEPAY = (
        "applepay",
        "Apple Pay",
        "Прием платежей с карт с помощью Apple Pay",
    )
    TINKOFFPAY = (
        "tinkoffpay",
        "Tinkoff Pay",
        "Прием платежей с карт с помощью Tinkoff Pay",
    )
    PAYPAL = (
        "paypal",
        "PayPal",
        "Крупнейший оператор электронных денежных средств во всем мире",
    )
    WEBMONEY = (
        "webmoney",
        "WebMoney Z",
        "Электронная платежная система. Приём средств с WMZ-кошельков",
    )
    USDT = (
        "usdt",
        "USDT-TRC20",
        "Прием платежей в USDT с криптокошельков в сети TRC-20",
    )
    MC = (
        "mc",
        "Мобильный платеж",
        "Оплата услуг посредством API/WEB формы. Мегафон",
    )

    def __new__(
        cls,
        value: str,
        title: str,
        processing: str,
    ):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._title_ = title
        obj._processing_ = processing
        return obj

    @property
    def title(self) -> str:
        return self._title_

    @property
    def processing(self) -> str:
        return self._processing_


class UnitPay:
    api_url: str
    project_id: int
    secret_key: str

    def __init__(self):
        self.api_url = config.UNIT_API_URL
        self.project_id = config.UNITPAY_PROJECT_ID
        self.secret_key = config.UNITPAY_SECRET_KEY

    async def register_paylink(
        self,
        amount: float,
        user_id: int,  # account
        username: str,
        bot_username: str,
        bot_token: str,
        currency: Currency = Currency.RUB,
        payment_system: UnitPaymentSystemCode = UnitPaymentSystemCode.CARD,
    ):
        method = UnitPayRequestMethod.INIT_PAYMENT

        params = {
            "account": user_id,
            "currency": currency.value,
            "desc": "Пополнение баланса",
            "payment_system": payment_system.value,
            "projectId": self.project_id,
            "resultUrl": f"{config.BOT_URL}/unitpay_redirect_to_bot?bot_username={bot_username}",  # noqa
            "sum": amount,
            "secretKey": self.secret_key,
        }

        params["signature"] = self.calculate_signature(
            params=params,
            method=method,
        )

        params_string = "&".join(
            [f"params[{key}]={value}" for key, value in params.items()]
        )

        query_string = f"method={method}&{params_string}"

        response = await http_request(
            url=f"self.api_url?{query_string}",
            http_method="GET",
        )

        response_data = response.json()

        if (
            "result" not in response_data
            or "type" not in response_data["result"]
        ):
            # Error
            pass

        result = response_data["result"]

        pay_url = (
            result["redirectUrl"]
            if result["type"] == "redirect"
            else result["receiptUrl"]
        )

        payment_id = result["paymentId"]

        save_paylink(
            user_id=user_id,
            order_id=f"{user_id}-{payment_id}",
            payment_gateway="unitpay",
            bot_token=bot_token,
            amount=sum,
        )

        return pay_url

    async def check_ipn_request(
        self,
        method: UnitPayCheckMethod,
        params: Dict[str, Any],
    ):
        if params.pop("signature") != self.calculate_signature(
            params=params,
            method=method,
        ):
            return "{'error': {'message': 'Неверная подпись!'}}"

        order_id = f"{params['account']}-{params['unitpayId']}"

        paylink_data = db.get_paylink_data_by_order_id(order_id)

        if not paylink_data:
            return "{'error': {'message': 'Платеж не найден!'}}"

        if method in (
            UnitPayCheckMethod.CHECK,
            UnitPayCheckMethod.PREAUTH,
            UnitPayCheckMethod.ERROR,
        ):
            return "{'result': {'message': 'Запрос успешно обработан'}}"

        if method != UnitPayCheckMethod.PAY:
            return "{'error': {'message': 'Неверный метод!'}}"

        if paylink_data["status"] == "paid":
            logger.warning("Order already paid! Order_id: %s", order_id)
            return "{'result': {'message': 'Запрос успешно обработан'}}"

        if paylink_data["amount"] != params["orderSum"]:
            return "{'error': {'message': 'Неверная сумма!'}}"

        if paylink_data["user_id"] != params["account"]:
            return "{'error': {'message': 'Неверный аккаунт!'}}"

        if paylink_data["currency"] != params["currency"]:
            return "{'error': {'message': 'Неверная валюта!'}}"

        user_id = paylink_data["user_id"]

        amount = params["orderSum"]

        db.update_user_balance(user_id, amount)
        db.set_paylink_paid(paylink_data["id"], amount)
        await db.Add_History(user_id, amount, "Пополнение - UnitPay")

        logger.info(
            "Successful payment! Payment Gateway: %s. Order_id: %s",
            "UnitPay",
            order_id,
        )

        bot = get_bot_by_id(paylink_data["bot_id"])

        await bot.send_message(
            chat_id=user_id,
            text=tm.message.wallet_success_payment().format(
                paylink_data["amount"],
                gateway_name="UnitPay",
            ),
            reply_markup=create_to_wallet_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        await bot.session.close()

        return "{'result': {'message': 'Запрос успешно обработан'}}"

    def calculate_signature(
        self,
        params: Dict[str, Any],
        method: UnitPayRequestMethod | None = None,
    ) -> str:
        params_string = "{up}".join(
            [method]
            if method
            else []
            + [
                str(value)
                for key, value in sorted(params.items())
                if key not in {"secretKey", "signature", "sign"}
            ]
            + [self.secret_key]
        )

        sign = hashlib.sha256(params_string.encode()).hexdigest()

        return sign


unitpay = UnitPay()
