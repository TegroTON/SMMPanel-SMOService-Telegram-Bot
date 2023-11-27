import logging
from typing import Any, Dict

import httpx
from httpx import USE_CLIENT_DEFAULT, BasicAuth, Response

logger = logging.getLogger(__name__)


async def http_request(
    url: str,
    data: Dict[str, Any] | None = None,
    json_data: Dict[str, Any] | None = None,
    http_method: str = "POST",
    headers: Dict[str, Any] | None = None,
    timeout: int = USE_CLIENT_DEFAULT,
    user: str | None = None,
    password: str | None = None,
) -> Response | None:
    if user and password:
        auth = BasicAuth(user, password)
    else:
        auth = USE_CLIENT_DEFAULT

    async with httpx.AsyncClient() as client:
        try:
            if http_method == "POST":
                response = await client.post(
                    url,
                    headers=headers,
                    data=data,
                    json=json_data,
                    timeout=timeout,
                    auth=auth,
                )
            else:
                response = await client.get(
                    url,
                    headers=headers,
                    params=data,
                )

            response.raise_for_status()

        except httpx.HTTPError as error:
            logger.error(f"HTTP error: {error}")
            logger.exception(error)
            response = None

    return response
