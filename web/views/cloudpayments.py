import logging
from http import client

from aiohttp.web import Request, Response

from core.payment_system.cloudpayments import cloudpayments

logger = logging.getLogger("CloudPayments")


async def ipn_handler(request: Request):
    headers = {key: value for key, value in request.headers.items()}
    bytes = await request.read()

    result = await cloudpayments.check_ipn(
        data=bytes,
        headers=headers,
    )

    return Response(
        status=client.OK,
        text=f'{{"code": {result}}}',
    )
