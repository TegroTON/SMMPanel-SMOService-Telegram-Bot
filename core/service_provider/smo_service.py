import asyncio
from typing import Any, Dict, List

import database as db
from core.config import config

from .provider import ServiceParseError, ServiceProvider, logger


class SmoServiceProvider(ServiceProvider):
    url = "https://smoservice.media/api/"
    name = "SmoService"

    def prepare_data_for_activate(
        self,
        service_id: int,
        url: str,
        quantity: int,
    ) -> Dict[str, Any]:
        return {
            "user_id": config.SMOSERVICE_USER_ID,
            "api_key": config.SMOSERVICE_KEY,
            "action": "create_order",
            "service_id": service_id,
            "url": url,
            "count": quantity,
        }

    def get_order_id_from_response(
        self,
        response_data: Dict[str, Any],
    ) -> int:
        if (
            "data" not in response_data
            or "order_id" not in response_data["data"]
        ):
            raise ValueError("Response not contains 'order'")

        return response_data["data"]["order_id"]

    async def _check_multiple_orders_status(
        self,
        orders_ids: List[int],
    ):
        for internal_id, external_id in orders_ids:
            await self.check_order_status(
                internal_id=internal_id,
                external_id=external_id,
            )

            await asyncio.sleep(0.1)

    def prepare_data_for_check(
        self,
        order_id: int,
    ) -> Dict[str, Any]:
        return {
            "user_id": config.SMOSERVICE_USER_ID,
            "api_key": config.SMOSERVICE_KEY,
            "action": "check_order",
            "order_id": order_id,
        }

    def get_order_data_from_response(
        self,
        response_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        if (
            "data" not in response_data
            or "order_id" not in response_data["data"]
            or "status" not in response_data["data"]
        ):
            raise ValueError(
                "Response not contains 'order' or 'status':\n"
                f"{response_data}"
            )

        return response_data["data"]

    def calculate_refund_amount(
        self,
        total_amount: float,
        quantity: int,
        data: Dict[str, Any],
    ) -> float:
        return total_amount

    def prepare_data_for_parse(self) -> Dict[str, Any]:
        return {
            "user_id": config.SMOSERVICE_USER_ID,
            "api_key": config.SMOSERVICE_KEY,
            "action": "services",
        }

    def get_data_for_parse(
        self,
        response_data: Dict[str, Any],
    ) -> Dict[int, Dict[str, Any]]:
        if "type" not in response_data or response_data["type"] == "error":
            raise ServiceParseError(
                (
                    f"Failed to parse services for {self.name}."
                    f" Wrong response: {response_data['desc']}."
                ),
                service_name=self.name,
                cause=response_data["desc"],
            )

        return {
            int(product_data["id"]): product_data
            for product_data in response_data["data"]
        }

    async def update_product(
        self,
        existing_product: Dict[str, Any],
        product: Dict[str, Any],
    ):
        if {
            existing_product["name"],
            existing_product["price"],
            existing_product["minorder"],
            existing_product["maxorder"],
        } == {
            product["name"],
            round(
                float(product["price"]),
                config.PRODUCT_PRICE_PRECISION,
            ),
            int(product["min"]),
            int(product["max"]),
        }:
            return

        db.update_product(
            service_id=product["id"],
            min_quantity=product["min"],
            max_quantity=product["max"],
            price=round(
                float(product["price"]),
                config.PRODUCT_PRICE_PRECISION,
            ),
        )
        logger.info("Product %s updated.", product["id"])

    async def parse_product_data(
        self,
        product_data: Dict[str, Any],
    ):
        category_name = product_data["root_category_name"]
        subcategory_name = product_data["category_name"]

        category_id = db.add_category(name=category_name)
        if subcategory_name:
            subcategory_id = db.add_category(
                name=subcategory_name,
                parent_id=category_id,
            )

        db.add_product(
            category_id=subcategory_id or category_id,
            name=product_data["name"],
            min_quantity=product_data["min"],
            max_quantity=product_data["max"],
            price=round(
                float(product_data["price"]),
                config.PRODUCT_PRICE_PRECISION,
            ),
            service_id=product_data["id"],
            service_provider=self.name,
        )
