from aiohttp.web import Application

from core.payment_system.cryptopay import crypto
from smoservice.forum import views


def setup_routes(app: Application):
    app.router.add_get("/", views.index)
    app.router.add_post("/cryptobot", crypto.get_updates)
    app.router.add_post("/tonwallet", views.ton_wallet_ipn_handler)
    app.router.add_post("/tegroSuccess", views.tegro_ipn_handler)
