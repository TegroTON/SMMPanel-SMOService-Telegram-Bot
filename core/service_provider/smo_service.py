import logging
from typing import Any, Dict, List

from validators import ValidationError

import database as db
from core.config import config

from .provider import ServiceParseError, ServiceProvider

logger = logging.getLogger(__name__)


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
            raise ValidationError("Response not contains 'order'")

        return response_data["data"]["order_id"]

    async def _check_multiple_orders_status(
        self,
        orders_ids: List[int],
    ):
        for internal_id, external_id in orders_ids:
            await self.try_check_order_status(
                internal_id=internal_id,
                external_id=external_id,
            )

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
            raise ValidationError(
                "Response not contains 'order' or 'status':\n"
                f"{response_data}"
            )

        return response_data["data"]

    def calculate_refund_amount(
        self,
        user_id: int,
        total_amount: float,
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
    ) -> Dict[str, Any]:
        if response_data["type"] == "error":
            raise ServiceParseError(
                (
                    f"Failed to parse services for {self.name}."
                    f" Wrong response: {response_data['desc']}."
                ),
                service_name=self.name,
                cause=response_data["desc"],
            )

        return response_data["data"]

    async def parse_product_data(
        self,
        product_data: Dict[str, Any],
    ):
        product_name = product_data["name"]
        min_quantity = product_data["min"]
        max_quantity = product_data["max"]
        category = product_data["root_category_name"]
        sub_category = product_data["category_name"]
        cost = product_data["price"]
        service_id = product_data["id"]

        if "telegram" in category or "телеграм" in category.lower():
            return

        await db.AddCategory(category, self.name)
        if sub_category != "":
            category_id = await db.GetIdParentCategory(
                category, self.name, None
            )
            await db.AddCategory(sub_category, self.name, category_id)
            parent_id = await db.GetIdParentCategory(
                sub_category, self.name, category_id
            )
        else:
            parent_id = await db.GetIdParentCategory(category, self.name, None)
        await db.AddProduct(
            parent_id,
            product_name,
            min_quantity,
            max_quantity,
            cost,
            service_id,
        )
