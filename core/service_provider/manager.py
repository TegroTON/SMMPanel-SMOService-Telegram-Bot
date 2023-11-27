from typing import Dict, List

import database as db
from core.callback_factories.my_orders import (
    MyOrdersAction,
    MyOrdersCallbackData,
)
from core.keyboards.utils import create_back_keyboard
from core.payment_system.utils import refund_user_balance
from core.service_provider.order_status import OrderStatus
from core.utils.bot import notify_user

from .provider import ServiceParseError, ServiceProvider, logger
from .service_provider_factory import service_provider_factory
from .smm_panel import SmmPanelProvider
from .smo_service import SmoServiceProvider


class ProviderManager:
    services: Dict[str, ServiceProvider] = {}

    def __init__(self):
        self._init_providers()
        self._load_services()

    def _init_providers(self):
        services = db.get_services()

        if services:
            return

        logger.info("Adding default service providers...")
        for service in [SmmPanelProvider, SmoServiceProvider]:
            db.add_service(service.name)

    def _load_services(self):
        for service_data in db.get_services():
            service = service_provider_factory.get_provider(
                service_data["name"]
            )
            if service_data["is_active"] == 0:
                service.deactivate()

            self.services[service_data["name"]] = service

    def activate_service(
        self,
        service: ServiceProvider | str,
    ):
        service = (
            service
            if isinstance(service, ServiceProvider)
            else service_provider_factory.get_provider(service)
        )

        if not service.is_active:
            logger.info("Activating service provider '%s'", service.name)

            service.activate()

            db.update_service_status(service.name, 1)

    def activate_all_services(self):
        logger.info("Activating all services...")
        services = db.get_services()

        for service_data in services:
            self.activate_service(service_data["name"])

    def deactivate_service(
        self,
        service: ServiceProvider | str,
    ):
        service = (
            service
            if isinstance(service, ServiceProvider)
            else service_provider_factory.get_provider(service)
        )

        if service.is_active:
            logger.info("Deactivating service provider '%s'", service.name)

            service.deactivate()

            db.update_service_status(service.name, 0)

    def toggle_service(
        self,
        service: str | ServiceProvider,
    ):
        service = (
            service
            if isinstance(service, ServiceProvider)
            else service_provider_factory.get_provider(service)
        )

        if service.is_active:
            self.deactivate_service(service)
        else:
            self.activate_service(service)

    def get_all_services(self) -> Dict[str, ServiceProvider]:
        return self.services.copy()

    def get_all_services_list(self) -> List[ServiceProvider]:
        return list(self.services.values())

    def get_active_services_list(self) -> List[ServiceProvider]:
        return [
            service
            for _, service in self.services.items()
            if service.is_active
        ]

    def get_active_services_names(self) -> List[str]:
        return [
            service.name
            for _, service in self.services.items()
            if service.is_active
        ]

    async def activate_order(
        self,
        order_id: int,
        service_name: str,
    ):
        logger.info("Activating order '%s' for '%s'", order_id, service_name)
        service_provider = service_provider_factory.get_provider(service_name)
        await service_provider.activate_order(order_id)

    async def check_order_status(
        self,
        order_id: int,
        external_order_id: int,
        service_name: str,
    ):
        logger.info("Checking order '%s' for '%s'", order_id, service_name)

        service_provider = service_provider_factory.get_provider(service_name)
        await service_provider.check_order_status(order_id, external_order_id)

    async def check_orders(self):
        logger.info("Checking orders...")

        for provider in self.get_active_services_list():
            try:
                logger.info("Checking orders for '%s'", provider.name)
                await provider.check_orders_status()
            except Exception as error:
                logger.error(error)
                logger.exception(error)

    async def activate_orders(self):
        logger.info("Starting orders...")
        for provider in self.get_active_services_list():
            provider: ServiceProvider
            orders = db.get_paid_orders(provider.name)

            if not orders:
                continue

            logger.info("Starting orders for '%s'", provider.name)
            for order in orders:
                try:
                    await provider.activate_order(order["id"])
                except Exception as error:
                    logger.error("Failed to activate order %s", order["id"])
                    logger.exception(error)

    async def update_services(self):
        logger.info("Updating services...")
        for provider in self.get_active_services_list():
            try:
                await provider.parse_services()
            except ServiceParseError as error:
                logger.error(error)
                logger.exception(error)

    async def cancel_order(
        self,
        order_id: int,
    ):
        logger.info("Cancelling order '%s'", order_id)

        order = db.get_order_by_id(order_id)

        if not order["order_id"] and order["status"] != OrderStatus.NEW:
            return

        db.update_order_status(
            order_id=order_id,
            status=OrderStatus.CANCELED,
        )

        await refund_user_balance(
            user_id=order["user_id"],
            amount=order["sum"],
            order_id=order_id,
        )

        await notify_user(
            user_id=order["user_id"],
            bot=order["bot_id"],
            message=(
                "🙁 Ваш заказ был отменен!\n"
                "💰 Возврат средств: <b>{refund_amount}</b> руб.\n"
            ).format(refund_amount=order["sum"]),
            reply_markup=create_back_keyboard(
                text="🛒 Перейти к заказу",
                data=MyOrdersCallbackData(
                    action=MyOrdersAction.VIEW_ORDER,
                    order_id=order_id,
                ),
            ),
        )


provider_manager = ProviderManager()
