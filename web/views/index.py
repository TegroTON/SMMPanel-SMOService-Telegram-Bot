import logging
from http import client

import aiohttp_jinja2
from aiohttp.web import Request

logger = logging.getLogger(__name__)


@aiohttp_jinja2.template("index.html")
async def index(request: Request):
    return {"status": client.OK}
