import logging
import sys
from os import getenv
from typing import Any, Dict, Union
from aiohttp import web
from finite_state_machine import form_router
from dotenv import load_dotenv
from core.handlers import StartCommand, SendAllAdmin, ReferralLink, Parsing, ListOrders, Help, FAQ, CreateAnOrder, \
    CheckGroup, Check, admin, AdmibGetAllOrders, AddOrRemoveCategory, Balance, CreateBot, Inline_Query, AdminGetService
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.utils.token import TokenValidationError, validate_token
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    TokenBasedRequestHandler,
    setup_application,
)
from aiogram.filters import StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

load_dotenv()
main_router = Router()
BASE_URL = getenv("BOT_URL")
WEB_HOOK_PORT = 443
MAIN_BOT_TOKEN = getenv("TOKEN")
WEB_SERVER_HOST = "localhost"
WEB_SERVER_PORT = 8001
MAIN_BOT_PATH = "/webhook/main"
OTHER_BOTS_PATH = "/webhook/bot/{bot_token}"
OTHER_BOTS_URL = f"{BASE_URL}{OTHER_BOTS_PATH}"
MAIN_BOT_URL = f"{BASE_URL}{MAIN_BOT_PATH}"

class FSMFillFrom(StatesGroup):
    get_bot_token = State()


async def on_startup(dispatcher: Dispatcher, bot: Bot):
    await bot.set_webhook(f"{MAIN_BOT_URL}")


def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    session = AiohttpSession()

    bot_settings = {"session": session, "parse_mode": ParseMode.HTML}
    bot = Bot(token=MAIN_BOT_TOKEN, **bot_settings)

    storage = MemoryStorage()

    main_dispatcher = Dispatcher(storage=storage)
    multibot_dispatcher = Dispatcher(storage=storage)

    main_dispatcher.include_routers(StartCommand.StartRouter, AddOrRemoveCategory.AddOrRemoveCategoryRouter,
                                    AdmibGetAllOrders.AdminAllOrders, admin.AdminRouter,
                                    Check.CheckRouter, CreateAnOrder.OrderRouter, CreateBot.NewBotRouter,
                                    FAQ.FAQRouter, Help.HelpRouter, Inline_Query.QueryRouter,
                                    ListOrders.ListOrders, Parsing.ParsingRouter, ReferralLink.ReferralRouter,
                                    SendAllAdmin.SendAllRouter, AdminGetService.AdminGetServiceRouter, Balance.BalanceRouter, main_router)
    main_dispatcher.startup.register(on_startup)

    multibot_dispatcher.include_router(form_router)

    app = web.Application()
    SimpleRequestHandler(dispatcher=main_dispatcher, bot=bot).register(app, path=MAIN_BOT_PATH)
    TokenBasedRequestHandler(
        dispatcher=main_dispatcher,
        bot_settings=bot_settings,
    ).register(app, path=OTHER_BOTS_PATH)

    setup_application(app, main_dispatcher, bot=bot)
    setup_application(app, multibot_dispatcher)

    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    main()