import asyncio

import aiohttp_jinja2
import jinja2
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    TokenBasedRequestHandler,
    setup_application,
)
from aiohttp import web

from core.config import config
from core.handlers import (
    FAQ,
    AddOrRemoveCategory,
    AdminGetAllOrders,
    AdminGetService,
    Check,
    CreateAnOrder,
    CreateBot,
    Inline_Query,
    ListOrders,
    Parsing,
    ReferralLink,
    SendAllAdmin,
    StartCommand,
    admin,
    my_orders,
    order_info,
    wallet,
)
from core.service_provider.manager import provider_manager
from core.utils.logger import init_logger

BASE_URL = config.BOT_URL
MAIN_BOT_TOKEN = config.BOT_TOKEN

WEB_SERVER_HOST = config.HOST
WEB_SERVER_PORT = config.PORT
MAIN_BOT_PATH = config.MAIN_BOT_PATH
OTHER_BOTS_PATH = config.OTHER_BOTS_PATH
OTHER_BOTS_URL = f"{BASE_URL}{OTHER_BOTS_PATH}"
MAIN_BOT_URL = f"{BASE_URL}{MAIN_BOT_PATH}"


class FSMFillFrom(StatesGroup):
    get_bot_token = State()


def setup_routes(application):
    from smoservice.forum.routes import setup_routes as setup_forum_routes

    setup_forum_routes(application)


def setup_external_libraries(application: web.Application) -> None:
    aiohttp_jinja2.setup(
        application,
        loader=jinja2.FileSystemLoader("./templates"),
    )


def setup_app(application):
    setup_external_libraries(application)
    setup_routes(application)


async def scheduler(period, fu, *args, **kw):
    while True:
        await asyncio.sleep(period)
        await fu(*args, **kw)


async def on_startup(dispatcher: Dispatcher, bot: Bot):
    await bot.set_webhook(f"{BASE_URL}{MAIN_BOT_PATH}")

    loop = asyncio.get_event_loop()
    loop.create_task(
        scheduler(
            config.CHECK_ORDER_STATUS_INTERVAL,
            provider_manager.check_orders,
        )
    )
    loop.create_task(
        scheduler(
            config.AUTO_STARTING_ORDERS_INTERVAL,
            provider_manager.activate_orders,
        )
    )


def main():
    init_logger()

    session = AiohttpSession()
    bot_settings = {"session": session, "parse_mode": ParseMode.HTML}
    bot = Bot(token=MAIN_BOT_TOKEN, **bot_settings)
    storage = MemoryStorage()

    main_dispatcher = Dispatcher(storage=storage)
    multibot_dispatcher = Dispatcher(storage=storage)

    main_dispatcher.include_routers(
        StartCommand.start_router,
        admin.AdminRouter,
        CreateAnOrder.order_router,
        FAQ.FAQRouter,
        Inline_Query.QueryRouter,
        ListOrders.ListOrders,
        Parsing.ParsingRouter,
        ReferralLink.referral_router,
        SendAllAdmin.SendAllRouter,
        AdminGetService.AdminGetServiceRouter,
        CreateBot.NewBotRouter,
        AddOrRemoveCategory.AddOrRemoveCategoryRouter,
        AdminGetAllOrders.AdminAllOrders,
        Check.check_router,
        wallet.balance_router,
        my_orders.my_orders_router,
        order_info.order_info_router,
    )

    main_dispatcher.startup.register(on_startup)

    app = web.Application()
    setup_app(app)
    SimpleRequestHandler(dispatcher=main_dispatcher, bot=bot).register(
        app, path=MAIN_BOT_PATH
    )
    # TODO: This is not safe solution for multibots.
    TokenBasedRequestHandler(
        dispatcher=main_dispatcher,
        bot_settings=bot_settings,
    ).register(app, path=OTHER_BOTS_PATH)

    setup_application(app, main_dispatcher, bot=bot)
    setup_application(app, multibot_dispatcher)

    app.router.add_static(
        "/static/",
        path="./static",
        name="static",
    )
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    main()
