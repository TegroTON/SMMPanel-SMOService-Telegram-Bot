import logging
from typing import Dict, List

import database as db

from .provider import ServiceProvider
from .service_provider_factory import service_provider_factory
from .smm_panel import SmmPanelProvider
from .smo_service import SmoServiceProvider

logger = logging.getLogger(__name__)


class ProviderManager:
    active_services: Dict[str, ServiceProvider]

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
        self.active_services = {
            service["name"]: service_provider_factory.get_provider(
                service["name"]
            )
            for service in db.get_active_services()
        }

    def activate_service_provider(
        self,
        service_provider: ServiceProvider | str,
    ):
        name = (
            service_provider.name
            if isinstance(service_provider, ServiceProvider)
            else service_provider
        )

        if name not in self.active_services:
            logger.info("Activating service provider '%s'", service_provider)
            self.active_services[name] = service_provider_factory.get_provider(
                name
            )
            db.update_service_status(name, 1)

    def activate_all_services(self):
        logger.info("Activating all services...")
        services = db.get_services()

        for service in services:
            if service["name"] in self.active_services:
                continue

            db.update_service_status(service["name"], 1)
            self.active_services[
                service["name"]
            ] = service_provider_factory.get_provider(service["name"])
            logger.info("Activated service '%s'", service["name"])

    def deactivate_service(
        self,
        service_provider: ServiceProvider | str,
    ):
        name = (
            service_provider.name
            if isinstance(service_provider, ServiceProvider)
            else service_provider
        )

        if name in self.active_services:
            logger.info("Deactivating service provider '%s'", service_provider)
            db.update_service_status(name, 0)
            self.active_services.pop(name)

    def get_active_services_list(self) -> List[ServiceProvider]:
        return list(self.active_services.values())

    def get_active_services_names(self) -> List[str]:
        return list(self.active_services.keys())

    async def activate_order(
        self,
        order_id: int,
        service_name: str,
    ):
        logger.info("Activating order '%s' for '%s'", order_id, service_name)
        service_provider = service_provider_factory.get_provider(service_name)
        await service_provider.try_activate_order(order_id)

    async def check_orders(self):
        logger.info("Checking orders...")
        for provider in self.get_active_services_list():
            try:
                logger.info("Checking orders for '%s'", provider.name)
                await provider.try_check_orders_status()
            except Exception as error:
                logger.error(error)
                logger.exception(error)

    async def activate_orders(self):
        logger.info("Starting orders...")
        for _, provider in self.active_services.items():
            provider: ServiceProvider
            orders = db.get_paid_orders(provider.name)

            if not orders:
                continue

            logger.info("Starting orders for '%s'", provider.name)
            for order in orders:
                try:
                    await provider.try_activate_order(order["id"])
                except Exception as error:
                    logger.error("Failed to activate order %s", order["id"])
                    logger.exception(error)


provider_manager = ProviderManager()
