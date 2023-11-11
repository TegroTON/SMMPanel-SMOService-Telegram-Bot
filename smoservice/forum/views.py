import aiohttp
import aiohttp_jinja2
from aiohttp.web import Request

from core.payment_system.tegro_money import tegro_success
from core.payment_system.ton_wallet import ton_wallet_success


@aiohttp_jinja2.template("index.html")
async def index(request: Request):
    return {"status": 200}


async def tegro_ipn_handler(request: Request):
    reader = aiohttp.MultipartReader(
        headers=request.headers, content=request.content
    )
    response_data = {}
    while part := await reader.next():
        response_data[part.name] = await part.text()

    await reader.release()

    await tegro_success(response_data)
    return {"status": 200}


async def ton_wallet_ipn_handler(request):
    await ton_wallet_success(request)
    return {"status": 200}
