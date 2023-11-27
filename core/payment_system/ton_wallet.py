import uuid

from core.config import config
from core.utils.http import http_request


async def ton_wallet_success(request):
    for event in request.get_json():
        if event["type"] == "ORDER_PAID":
            data = event["payload"]
            print(
                "Оплачен счет N {} на сумму {} {}. Оплата {} {}.".format(
                    data["externalId"],
                    data["orderAmount"][
                        "amount"
                    ],  # Сумма счета, указанная при создании ссылки для оплаты
                    data["orderAmount"]["currencyCode"],  # Валюта счета
                    data["selectedPaymentOption"]["amount"][
                        "amount"
                    ],  # Сколько оплатил покупатель
                    data["selectedPaymentOption"]["amount"][
                        "currencyCode"
                    ],  # В какой криптовалюте
                )
            )


async def register_ton_wallet_paylink(
    amount: float,
    user_id: int,
    bot_username: str,
) -> str | None:
    headers = {
        "Wpay-Store-Api-Key": config.WPAY_STORE_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    order_id = uuid.uuid4()

    payload = {
        "amount": {
            "amount": amount,
            "currencyCode": "RUB",
        },
        "description": "Goods and service.",
        "externalId": f"{order_id}",
        "timeoutSeconds": 60 * 60 * 24,
        "customerTelegramUserId": user_id,
        "returnUrl": f"https://t.me/{bot_username}",
        "failReturnUrl": "https://t.me/wallet",
    }

    response = await http_request(
        url="https://pay.wallet.tg/wpay/store-api/v1/order",
        json_data=payload,
        headers=headers,
    )

    if not response:
        return ""

    response_data = response.json()

    if not response_data or not response_data.get("data"):
        return ""

    direct_paylink = response_data["data"]["payLink"]

    return direct_paylink
