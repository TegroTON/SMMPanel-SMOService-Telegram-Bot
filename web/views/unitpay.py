import logging

import aiohttp
from aiohttp.web import Request, Response

from core.payment_system.unitpay import UnitPayCheckMethod, unitpay
from core.utils.http import http_request

logger = logging.getLogger("Unitpay")


async def unitpay_redirect_to_bot(request):
    request_data = dict(request.query.items())

    raise aiohttp.web.HTTPFound(f"https://t.me/{request_data['bot_username']}")


async def unitpay_ipn_handler(request: Request):
    query_data = dict(request.query.items())
    method = query_data.get("method")
    params = {
        key.replace("params[", "").replace("]", ""): value
        for key, value in query_data.items()
        if key.startswith("params[")
    }

    if not method or not params:
        logger.warning("UnitPay - Bad IPN request.\n  Data: '%s'", query_data)
        return Response(
            text='{"error": {"message": "Request is not contains method or params"}}',  # noqa
            content_type="application/json",
        )

    try:
        method = UnitPayCheckMethod(method)
    except ValueError:
        logger.warning("UnitPay - Bad IPN request.\n  Data: '%s'", query_data)
        return Response(
            text='{"error": {"message": "Bad method"}}',
            content_type="application/json",
        )

    result = await unitpay.check_ipn_request(method, params)

    return Response(text=result, content_type="application/json")


async def unitpay_ipn_handler_r(request: Request):
    query = request.query_string

    dev_response = await http_request(
        url=f"https://koala-neutral-jolly.ngrok-free.app/unitpay_ipn?{query}",
        http_method="GET",
    )

    return Response(text=dev_response.text, content_type="application/json")


async def unitpay_create_order_r(request: Request):
    query_string = request.query_string

    unitpay_response = await http_request(
        url=f"https://unitpay.ru/api?{query_string}",
        http_method="GET",
    )

    return unitpay_response
