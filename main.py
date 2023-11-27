import asyncio
import logging
from datetime import datetime

import aiohttp_jinja2
import jinja2
from aiogram import Bot, Dispatcher, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.i18n import I18n
from aiogram.utils.i18n.middleware import ConstI18nMiddleware
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    TokenBasedRequestHandler,
    setup_application,
)
from aiohttp import web

from core.config import config
from core.filters import IsChatIsPrivate
from core.handlers import cheques, start
from core.utils.logger import init_logger

logger = logging.getLogger(__name__)

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
    from web.routes import setup_routes as setup_forum_routes

    setup_forum_routes(application)


def setup_external_libraries(application: web.Application) -> None:
    aiohttp_jinja2.setup(
        application,
        loader=jinja2.FileSystemLoader("./templates"),
    )


def setup_app(application):
    setup_external_libraries(application)
    setup_routes(application)


async def periodic_scheduler(period, fu, *args, **kw):
    while True:
        await asyncio.sleep(period)
        await fu(*args, **kw)


async def on_time_scheduler(start_time: datetime, fu, *args, **kw):
    start_time = start_time.time()
    while True:
        current_time = datetime.now().time()
        if (
            current_time.hour * 60 * 60
            + current_time.minute * 60
            + current_time.second
        ) - (
            start_time.hour * 60 * 60
            + start_time.minute * 60
            + start_time.second
        ) < 60:
            await fu(*args, **kw)
        await asyncio.sleep(60)


async def on_startup(dispatcher: Dispatcher, bot: Bot):
    from core.service_provider.manager import provider_manager

    try:
        await bot.set_webhook(f"{BASE_URL}{MAIN_BOT_PATH}")
    except TelegramUnauthorizedError as error:
        logger.critical("Main bot token revoked! Can't set webhook!")
        logger.exception(error)
        await bot.session.close()

    loop = asyncio.get_event_loop()
    loop.create_task(
        periodic_scheduler(
            config.CHECK_ORDER_STATUS_INTERVAL,
            provider_manager.check_orders,
        )
    )
    loop.create_task(
        periodic_scheduler(
            config.AUTO_STARTING_ORDERS_INTERVAL,
            provider_manager.activate_orders,
        )
    )
    loop.create_task(
        on_time_scheduler(
            # config.UPDATE_SERVICES_INTERVAL,
            datetime(year=2023, month=1, day=1, hour=0, minute=0, second=0),
            provider_manager.update_services,
        )
    )


def init_routers(main_dispatcher: Dispatcher):
    from core.handlers import (
        admin,
        common,
        my_bots,
        my_orders,
        new_order,
        order_info,
        referrals,
        wallet,
    )

    private_router = Router(name="private_chat_router")
    private_router.message.filter(IsChatIsPrivate())
    private_router.callback_query.filter(IsChatIsPrivate())
    private_router.include_routers(
        start.start_router,
        admin.admin_router,
        new_order.order_router,
        referrals.referral_router,
        my_bots.my_bots_router,
        cheques.check_router,
        wallet.balance_router,
        my_orders.my_orders_router,
        order_info.order_info_router,
    )

    main_dispatcher.include_routers(
        private_router,
        common.common_router,
    )


def main():
    init_logger()

    i18n = I18n(
        path="locales",
        default_locale="ru_RU",
        domain="messages",
    )

    I18n.set_current(i18n)

    session = AiohttpSession()
    bot_settings = {
        "session": session,
        "parse_mode": ParseMode.HTML,
    }

    bot = Bot(token=MAIN_BOT_TOKEN, **bot_settings)

    storage = MemoryStorage()
    i18n_middleware = ConstI18nMiddleware(
        i18n=i18n,
        locale="ru_RU",
    )

    main_dispatcher = Dispatcher(storage=storage)
    main_dispatcher.update.middleware(i18n_middleware)

    multibot_dispatcher = Dispatcher(storage=storage)
    multibot_dispatcher.update.middleware(i18n_middleware)

    init_routers(main_dispatcher)

    main_dispatcher.startup.register(on_startup)

    app = web.Application()
    setup_app(app)
    SimpleRequestHandler(
        dispatcher=main_dispatcher,
        bot=bot,
    ).register(app, path=MAIN_BOT_PATH)

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
