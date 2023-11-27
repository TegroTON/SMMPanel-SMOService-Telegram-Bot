from aiohttp.web import Application

from core.payment_system.cryptopay import cryptopay
from .views import cloudpayments, tegro_money, index


def setup_routes(app: Application):
    app.router.add_get("/", index.index)

    app.router.add_get("/tegroSuccess", tegro_money.tegro_success_redirect)
    app.router.add_get("/tegroFail", tegro_money.tegro_success_redirect)
    app.router.add_get("/tegro_ipn", tegro_money.ipn_handler)
    app.router.add_post("/tegro_ipn", tegro_money.ipn_handler)

    app.router.add_post("/cryptobot", cryptopay.crypto_api.get_updates)

    app.router.add_post("/cloudpayments_ipn", cloudpayments.ipn_handler)
