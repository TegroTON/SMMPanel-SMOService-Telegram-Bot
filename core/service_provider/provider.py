import logging
from abc import ABCMeta, abstractmethod
from typing import Any, Dict, List

from validators import ValidationError

import database as db
from core.callback_factories.my_orders import (
    MyOrdersAction,
    MyOrdersCallbackData,
)
from core.config import config
from core.keyboards.utils import create_back_keyboard
from core.payment_system.utils import (
    refund_user_balance,
    replenish_affiliate_balance,
)
from core.service_provider.order_status import OrderStatus
from core.utils.bot import get_bot_by_id, notify_user
from core.utils.http import http_request

logger = logging.getLogger(__name__)


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

    async def try_activate_order(
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
            except ValidationError:
                logger.error(
                    "Failed to activate order %s for service %s. Response: %s",
                    internal_order_id,
                    self.name,
                    response_data,
                )

                await notify_user(
                    user_id=config.ADMIN_ID,
                    bot_id=-1,
                    text=(
                        f"Проблема с активацией заказа {internal_order_id}.\n"
                    ),
                )

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

    async def try_check_orders_status(self):
        orders_ids = db.get_orders_ids_for_check(self.name)

        await self._check_multiple_orders_status(orders_ids=orders_ids)

    @abstractmethod
    async def _check_multiple_orders_status(
        self,
        orders_ids: List[int],
    ):
        pass

    async def try_check_order_status(
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
        except ValidationError:
            logger.error(
                "Failed to check order %s status. Response: %s.",
                internal_id,
                response_data,
            )
            return

        await self.update_check_status(
            data=data,
            internal_id=internal_id,
        )

    async def update_check_status(
        self,
        data: Dict[str, Any],
        internal_id: int,
    ):
        status = data["status"]

        if status == OrderStatus.IN_PROGRESS:
            db.update_order_status(
                order_id=internal_id,
                status=OrderStatus.IN_PROGRESS,
            )
            return

        if status not in [
            OrderStatus.COMPLETED,
            OrderStatus.PARTIAL,
            OrderStatus.CANCELED,
        ]:
            # Do nothing.
            return

        status = OrderStatus.from_ru(status)

        order = db.get_order_by_id(internal_id)

        db.update_order_status(
            order_id=internal_id,
            status=status,
        )

        message = (
            f"Статус заказа номер {internal_id}"
            f" изменен на '{status.title_ru}'\n"
        )

        affiliate_bonus_base_amount = order["sum"]

        if status in [OrderStatus.CANCELED, OrderStatus.PARTIAL]:
            refund_amount = self.calculate_refund_amount(
                user_id=order["user_id"],
                total_amount=order["sum"],
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
                message += f"Возврат средств: + {refund_amount}"

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
                text="Перейти к заказу",
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
        user_id: int,
        total_amount: float,
        data: Dict[str, Any],
    ) -> float:
        pass

    async def parse_services(self):
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
            data = self.get_data_for_parse(response_data)
        except ServiceParseError as error:
            logger.error(error)
            raise error

        for product_data in data:
            await self.parse_product_data(product_data)

        logger.info(f"Service '{self.name}' parsed successfully")
        return self.name

    @abstractmethod
    def prepare_data_for_parse(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_data_for_parse(
        self,
        response_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def parse_product_data(
        self,
        product_data: Dict[str, Any],
    ):
        pass
