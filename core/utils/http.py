import logging
from typing import Any, Dict

import httpx
from httpx import Response

logger = logging.getLogger(__name__)


async def http_request(
    url: str,
    data: Dict[str, Any] | None = None,
    http_method: str = "POST",
) -> Response | None:
    async with httpx.AsyncClient() as client:
        try:
            if http_method == "POST":
                response = await client.post(url, data=data)
            else:
                response = await client.get(url, params=data)

            response.raise_for_status()

            return response
        except httpx.HTTPError as error:
            logger.error(f"HTTP error: {error}")
            logger.exception(error)
            return None
