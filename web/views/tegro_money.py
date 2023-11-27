import logging
from http import client

import aiohttp
from aiohttp.web import Request, Response

import database as db
from core.payment_system.tegro_money import tegro_money
from core.utils.bot import get_bot_by_id

logger = logging.getLogger("TegroMoney")


async def ipn_handler(request: Request):
    if request.method == "POST":
        logging.info("Handling IPN request. POST.")
        reader = aiohttp.MultipartReader(
            headers=request.headers, content=request.content
        )
        request_data = {}
        while part := await reader.next():
            request_data[part.name] = await part.text()

        await reader.release()
    elif request.method == "GET":
        logging.info("Handling IPN request. GET.")
        request_data = dict(request.query.items())

    if not request_data or not {
        "order_id",
        "status",
        "amount",
        "sign",
    }.issubset(request_data.keys()):
        response_data = f'{"status": {client.BAD_REQUEST}}'
        logger.warning(
            "Bad IPN request.\n  Data: '%s'\n  Response: %s",
            request_data,
            response_data,
        )
        return Response(text=response_data, content_type="application/json")

    await tegro_money.check_ipn_request(request_data)
    return Response(
        text=f'{{"status": {client.OK}}}', content_type="application/json"
    )


async def tegro_success_redirect(request):
    request_data = dict(request.query.items())

    paylink = db.get_paylink_data_by_order_id(request_data["order_id"])

    bot = get_bot_by_id(paylink["bot_id"])
    bot_username = (await bot.get_me()).username

    await bot.session.close()

    raise aiohttp.web.HTTPFound(f"https://t.me/{bot_username}")
