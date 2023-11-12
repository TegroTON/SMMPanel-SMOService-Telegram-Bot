# from .provider import ServiceProvider


# async def try_activate_order(order_id: int, service_name: str):
#     service_provider: ServiceProvider = _providers[service_name]()
#     await service_provider.try_activate_order(order_id)


# async def check_orders():
#     for provider in _providers.values():
#         await provider().try_check_orders_status()


# __all__ = [
#     "ServiceProvider",
#     "SmmPanelProvider",
#     "SmoServiceProvider",
#     "try_activate_order",
#     "check_orders",
# ]
