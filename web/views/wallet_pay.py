import logging
from http import client

from aiohttp.web import Request, Response

from core.payment_system.ton_wallet import ton_wallet_success
from core.utils.http import http_request

logger = logging.getLogger("WalletPay")


async def wallet_ipn_handler(request):
    await ton_wallet_success(request)
    return {"status": client.OK}


async def wallet_ipn_handler_r(request: Request):
    dev_response = await http_request(
        url="https://koala-neutral-jolly.ngrok-free.app/wallet_ipn",
        data=request.json(),
        http_method="POST",
    )

    print(dev_response.text)

    return Response(text=dev_response.text, content_type="application/json")
