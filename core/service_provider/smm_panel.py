from typing import Any, Dict, List

import database as db
from core.config import config
from core.utils.coingecko_api import get_usd_rub_rate

from .provider import ServiceParseError, ServiceProvider, logger


class SmmPanelProvider(ServiceProvider):
    url: str = "https://smmpanel.ru/api/v1"
    name: str = "SmmPanel"
    usd_rub_rate: float = config.BASE_USD_RUB_RATE

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
            raise ValueError("Response not contains 'order'")

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
                await self.update_order_status(
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
            raise ValueError(
                "Response not contains 'status' or 'charge' or 'start_count'"
                " or 'remains':\n"
                f"{response_data}"
            )

        return response_data

    def calculate_refund_amount(
        self,
        total_amount: float,
        quantity: int,
        data: Dict[str, Any],
    ) -> float:
        remains = int(data["remains"])
        if remains == 0:
            return 0

        return round(
            total_amount / quantity * remains,
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
    ) -> Dict[int, Dict[str, Any]]:
        if "error" in response_data:
            raise ServiceParseError(
                (
                    f"Failed to parse services for {self.name}."
                    f" Wrong response: {response_data['error']}."
                ),
                service_name=self.name,
                cause=response_data["error"],
            )

        return {
            int(product_data["service"]): product_data
            for product_data in response_data
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
            await self.calc_price(product["rate"]),
            int(product["min"]),
            int(product["max"]),
        }:
            return

        db.update_product(
            service_id=product["service"],
            min_quantity=product["min"],
            max_quantity=product["max"],
            price=await self.calc_price(product["rate"]),
        )
        logger.info("Product %s updated.", product["service"])

    async def parse_product_data(
        self,
        product_data: Dict[str, Any],
    ):
        category_id = db.add_category(name=product_data["category"])
        db.add_product(
            category_id=category_id,
            name=product_data["name"],
            min_quantity=product_data["min"],
            max_quantity=product_data["max"],
            price=await self.calc_price(product_data["rate"]),
            service_id=product_data["service"],
            service_provider=self.name,
        )

    async def calc_price(
        self,
        charge: float,
    ) -> float:
        return round(
            float(charge) / config.CHARGE_PER_COUNT * self.usd_rub_rate,
            config.PRODUCT_PRICE_PRECISION,
        )

    async def parse_services(self) -> str:
        try:
            new_rate = await get_usd_rub_rate()
        except Exception as error:
            logger.error("Failed to parse %s.", self.name)
            logger.exception(error)

        if not self.usd_rub_rate or abs(self.usd_rub_rate - new_rate) > 1:
            self.usd_rub_rate = new_rate

        return await super().parse_services()
