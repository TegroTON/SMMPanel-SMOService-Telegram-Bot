import logging
from typing import Any, Dict, List

from validators import ValidationError

import database as db
from core.config import config

from .provider import ServiceParseError, ServiceProvider

logger = logging.getLogger(__name__)


class SmmPanelProvider(ServiceProvider):
    url = "https://smmpanel.ru/api/v1"
    name = "SmmPanel"

    def prepare_data_for_activate(
        self,
        service_id: int,
        url: str,
        quantity: int,
    ) -> Dict[str, Any]:
        return {
            "key": config.SMMPANEL_KEY,
            "action": "add",
            "service": service_id,
            "link": url,
            "quantity": quantity,
        }

    def get_order_id_from_response(
        self,
        response_data: Dict[str, Any],
    ) -> int:
        if "order" not in response_data:
            raise ValidationError("Response not contains 'order'")

        return response_data["order"]

    async def _check_multiple_orders_status(self, orders_ids: List[int]):
        for i in range(0, len(orders_ids), 100):
            ids_group = orders_ids[i : i + 100]  # noqa
            ids_dict = {key: value for (value, key) in ids_group}
            ids = list(map(str, ids_dict.keys()))

            data = {
                "key": config.SMMPANEL_KEY,
                "action": "status",
                "orders": ",".join(ids),
            }

            response_data = await self.make_request(data)

            if not response_data:
                logger.error("Failed to check orders statuses. No response.")
                continue

            if "error" in response_data:
                logger.error(
                    "Failed to check orders status. Response: %s",
                    response_data,
                )
                continue

            for external_id, status_data in response_data.items():
                await self.update_check_status(
                    data=status_data,
                    internal_id=ids_dict[int(external_id)],
                )

    def prepare_data_for_check(
        self,
        order_id: int,
    ):
        return {
            "key": config.SMMPANEL_KEY,
            "action": "status",
            "order": order_id,
        }

    def get_order_data_from_response(
        self,
        response_data: Dict[str, Any],
    ):
        if (
            "status" not in response_data
            or "charge" not in response_data
            or "start_count" not in response_data
            or "remains" not in response_data
        ):
            raise ValidationError(
                "Response not contains 'status' or 'charge' or 'start_count'"
                " or 'remains':\n"
                f"{response_data}"
            )

        return response_data

    def calculate_refund_amount(
        self,
        user_id: int,
        total_amount: float,
        data: Dict[str, Any],
    ) -> float:
        return round(
            float(data["charge"]) * float(data["remains"]),
            config.BALANCE_PRECISION,
        )

    def prepare_data_for_parse(self) -> Dict[str, Any]:
        return {
            "key": config.SMMPANEL_KEY,
            "action": "services",
        }

    def get_data_for_parse(
        self,
        response_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        if "error" in response_data:
            raise ServiceParseError(
                (
                    f"Failed to parse services for {self.name}."
                    f" Wrong response: {response_data['error']}."
                ),
                service_name=self.name,
                cause=response_data["error"],
            )

        return response_data

    async def parse_product_data(
        self,
        product_data: Dict[str, Any],
    ):
        category = product_data["category"]
        product_name = product_data["name"]
        min_quantity = product_data["min"]
        max_quantity = product_data["max"]
        charge = product_data["rate"]
        cost = round(
            float(charge) / config.CHARGE_PER_COUNT * config.USD_RUB_RATE,
            config.BALANCE_PRECISION,
        )
        service_id = product_data["service"]

        if "telegram" in category or "телеграм" in category.lower():
            return

        await db.AddCategory(category, self.name)
        parent_id = await db.GetIdParentCategory(category, self.name, None)
        await db.AddProduct(
            parent_id,
            product_name,
            min_quantity,
            max_quantity,
            cost,
            service_id,
        )
