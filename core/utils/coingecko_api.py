import asyncio
from .http import http_request


api_url = "https://api.coingecko.com/api/v3/simple/price"


async def get_usd_rub_rate() -> float:
    return await get_token_price(
        token="tether",
        currency="rub",
    )


async def get_token_price(
    token: str,
    currency: str,
) -> float:
    tries_left = 3

    while tries_left:
        tries_left -= 1
        response = await http_request(
            url=api_url,
            data={
                "ids": token,
                "vs_currencies": currency,
            },
            http_method="GET",
        )
        response_data = response.json()
        if token in response_data and currency in response_data[token]:
            return response_data[token][currency]

        await asyncio.sleep(1)

    raise Exception("Failed to get token price. (%s, %s)", token, currency)
