# TODO: This is just a temporary solution.
import os

from dotenv import load_dotenv

load_dotenv()

Service = "SmoService"

# Server
BOT_URL = os.getenv("BOT_URL")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")


# Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
MAIN_BOT_PATH = os.getenv("MAIN_BOT_PATH")
OTHER_BOTS_PATH = os.getenv("OTHER_BOTS_PATH")


# Debug
DEBUG = True if os.getenv("DEBUG") == 1 else False

# Cryptobot
CRYPTO_TOKEN = os.getenv("CRYPTO_TOKEN")
CRYPTO_TOKEN_TEST = os.getenv("CRYPTO_TOKEN_TEST")

# Ton wallet
WPAY_STORE_API_KEY = os.getenv("WPAY_STORE_API_KEY")

# Tegro money
TEGRO_SHOP_ID = os.getenv("TEGRO_SHOP_ID")
TEGRO_SECRET_KEY = os.getenv("TEGRO_SECRET_KEY")

# SmmPanel
SMMPANEL_KEY = os.getenv("SMMPANEL_KEY")
CHARGE_PER_COUNT = 1000

# SmoService
SMOSERVICE_KEY = os.getenv("SMOSERVICE_KEY")
SMOSERVICE_USER_ID = os.getenv("SMOSERVICE_USER_ID")

# Constants
REPLENISH_AMOUNT_VARIANTS = [250, 500, 1000, 5000, 10000, 25000]
MIN_REPLENISH_AMOUNT = 1

CHECK_MIN_SUM = 0.1
CHECK_CREDIT_PER_SUBSCRIBE = 10
BALANCE_PRECISION = 2

PAGINATION_CHECKS_PER_PAGE = 10
PAGINATION_CATEGORIES_PER_PAGE = 10

NEW_REFERRAL_BONUS = 5
REFERRAL_REPLENISH_BONUS_PERCENTS = [12, 4]

USD_RUB_RATE = 95

CHECK_ORDER_STATUS_INTERVAL = int(os.getenv("CHECK_ORDER_STATUS_INTERVAL"))
AUTO_STARTING_ORDERS_INTERVAL = int(os.getenv("AUTO_STARTING_ORDERS_INTERVAL"))
