import asyncio
from abc import ABCMeta, abstractmethod
from typing import Any, Dict, List
from core.utils.logger import create_logger

import database as db
from core.callback_factories.my_orders import (
    MyOrdersAction,
    MyOrdersCallbackData,
)
from core.keyboards.utils import create_back_keyboard
from core.payment_system.utils import (
    refund_user_balance,
    replenish_affiliate_balance,
)
from core.service_provider.order_status import OrderStatus
from core.utils.bot import get_bot_by_id, notify_user
from core.utils.http import http_request

logger = create_logger("ServicesProvider")


class ServiceParseError(Exception):
    service_name: str
    cause: str

    def __init__(
        self,
        *args: object,
        service_name: str,
        cause: str,
    ) -> None:
        super().__init__(*args)
        self.service_name = service_name
        self.cause = cause


class ServiceProvider(metaclass=ABCMeta):
    url: str
    name: str
    is_active: bool = True

    def deactivate(self):
        self.is_active = False

    def activate(self):
        self.is_active = True

    async def activate_order(
        self,
        internal_order_id: int,
    ):
        order = db.get_order_by_id(internal_order_id)

        data = self.prepare_data_for_activate(
            service_id=order["service_id"],
            url=order["url"],
            quantity=order["quantity"],
        )

        response_data = await self.make_request(data)
        if response_data:
            try:
                external_order_id = self.get_order_id_from_response(
                    response_data
                )
            except ValueError:
                logger.error(
                    "Failed to activate order %s for service %s. Response: %s",
                    internal_order_id,
                    self.name,
                    response_data,
                )

                return

            db.update_order_status_and_external_id(
                order_id=order["id"],
                status=OrderStatus.STARTING,
                external_id=external_order_id,
            )
            return

    @abstractmethod
    def prepare_data_for_activate(
        self,
        service_id: int,
        url: str,
        quantity: int,
    ) -> Dict[str, Any]:
        pass

    async def make_request(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any] | List[Any]:
        response = await http_request(self.url, data)
        if not response:
            return {"error": "Request failed"}
        return response.json()

    @abstractmethod
    def get_order_id_from_response(
        self,
        response_data: Dict[str, Any],
    ) -> int:
        pass

    async def check_orders_status(self):
        orders_ids = db.get_orders_ids_for_check(self.name)

        await self._check_multiple_orders_status(orders_ids=orders_ids)

    @abstractmethod
    async def _check_multiple_orders_status(
        self,
        orders_ids: List[int],
    ):
        pass

    async def check_order_status(
        self,
        internal_id: int,
        external_id: int,
    ):
        data = self.prepare_data_for_check(
            order_id=external_id,
        )

        response_data = await self.make_request(data)
        if not response_data:
            logger.error(
                "Failed to check order %s status. No response.",
                internal_id,
            )
            return
        try:
            data = self.get_order_data_from_response(response_data)
        except ValueError:
            logger.error(
                "Failed to check order %s status. Response: %s.",
                internal_id,
                response_data,
            )
            return

        await self.update_order_status(
            data=data,
            internal_id=internal_id,
        )

    async def update_order_status(
        self,
        data: Dict[str, Any],
        internal_id: int,
    ):
        status_text = data["status"]

        if status_text == OrderStatus.IN_PROGRESS:
            db.update_order_status(
                order_id=internal_id,
                status=OrderStatus.IN_PROGRESS,
            )
            return

        if status_text not in [
            OrderStatus.COMPLETED,
            OrderStatus.PARTIAL,
            OrderStatus.CANCELED,
        ]:
            # Do nothing.
            return

        status = OrderStatus.from_ru(status_text)

        order = db.get_order_by_id(internal_id)

        db.update_order_status(
            order_id=internal_id,
            status=status,
        )

        logger.info(
            "Order %s status changed to %s. Data: %s",
            internal_id,
            status,
            data,
        )

        message = (
            f"Статус заказа номер {internal_id} изменен: '{status.title_ru}'\n"
        )

        affiliate_bonus_base_amount = order["sum"]
        if status in [OrderStatus.CANCELED, OrderStatus.PARTIAL]:
            refund_amount = self.calculate_refund_amount(
                total_amount=order["sum"],
                quantity=order["quantity"],
                data=data,
            )
            if refund_amount:
                await refund_user_balance(
                    user_id=order["user_id"],
                    amount=refund_amount,
                    order_id=internal_id,
                    is_partial=status == OrderStatus.PARTIAL,
                )
                affiliate_bonus_base_amount -= refund_amount
                message += "💰 Возврат средств: {refund_amount} руб.\n".format(
                    refund_amount=refund_amount
                )

        bot = get_bot_by_id(order["bot_id"])

        if affiliate_bonus_base_amount > 0:
            await replenish_affiliate_balance(
                user_id=order["user_id"],
                amount=affiliate_bonus_base_amount,
                bot=bot,
            )

        await notify_user(
            user_id=order["user_id"],
            bot=bot,
            message=message,
            reply_markup=create_back_keyboard(
                data=MyOrdersCallbackData(
                    action=MyOrdersAction.VIEW_ORDER,
                    order_id=internal_id,
                ),
                text="🛒 Перейти к заказу",
            ),
        )

        await bot.session.close()

    @abstractmethod
    def prepare_data_for_check(
        self,
        order_id: int,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_order_data_from_response(
        self,
        response_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def calculate_refund_amount(
        self,
        total_amount: float,
        quantity: int,
        data: Dict[str, Any],
    ) -> float:
        pass

    async def parse_services(self) -> str:
        request_data = self.prepare_data_for_parse()

        response_data = await self.make_request(request_data)
        if not response_data:
            error = ServiceParseError(
                f"Failed to parse services for {self.name}. No response.",
                service_name=self.name,
                cause="Нет ответа от сервера",
            )
            logger.error(error)
            raise error

        try:
            new_products = self.get_data_for_parse(response_data)
        except ServiceParseError as error:
            logger.error(error)
            raise error

        exists_products_data = db.get_products(
            provider_name=self.name,
        )

        for existing_product_data in exists_products_data:
            await asyncio.sleep(0.0001)

            if existing_product_data["service_id"] not in new_products:
                db.set_product_is_active(
                    product_id=existing_product_data["id"],
                    is_active=False,
                )
                logger.warning(
                    "Service '%s' removed product '%s'",
                    self.name,
                    existing_product_data["service_id"],
                )
                continue
            if existing_product_data["service_id"] in new_products:
                new_product_data = new_products.pop(
                    existing_product_data["service_id"]
                )

                if not existing_product_data["is_active"]:
                    db.set_product_is_active(
                        product_id=existing_product_data["id"],
                        is_active=True,
                    )
                    logger.info(
                        "Service '%s' activated product '%s'",
                        self.name,
                        existing_product_data["service_id"],
                    )

                await self.update_product(
                    existing_product=existing_product_data,
                    product=new_product_data,
                )

        for product_data in new_products.values():
            await asyncio.sleep(0.0001)
            await self.parse_product_data(product_data)

        logger.info(f"Service '{self.name}' parsed successfully")
        return self.name

    @abstractmethod
    async def update_product(
        self,
        existing_product: Dict[str, Any],
        product: Dict[str, Any],
    ):
        pass

    @abstractmethod
    def prepare_data_for_parse(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_data_for_parse(
        self,
        response_data: Dict[str, Any],
    ) -> Dict[int, Dict[str, Any]]:
        pass

    @abstractmethod
    async def parse_product_data(
        self,
        product_data: Dict[str, Any],
    ):
        pass
