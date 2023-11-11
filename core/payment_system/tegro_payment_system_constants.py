from enum import IntEnum


class TegroPaymentSystem(IntEnum):
    YANDEX_MONEY = 5, "ЮMoney", "Процессинг - НКО ЮМани"
    QIWI = 14, "QIWI", "Процессинг - КИВИ Банк (АО)"
    PERFECT_MONEY_USD = 11, "Perfect Money USD", "Процессинг - Perfect Money"
    PERFECT_MONEY_EUR = 12, "Perfect Money EUR", "Процессинг - Perfect Money"
    PAYEER_RUB = 13, "Payeer RUB", "Процессинг - Payeer"
    BANK_CARDS_QIWI = 15, "Банковские карты", "Процессинг - КИВИ Банк (АО)"
    BITCOIN = 16, "Bitcoin", "Процессинг - Tegro.money"
    LITECOIN = 17, "Litecoin", "Процессинг - Tegro.money"
    ETHEREUM = 18, "Ethereum", "Процессинг - Tegro.money"
    APPLE_PAY = 19, "Apple Pay", "Процессинг - НКО ЮМани"
    QIWI_PERSONAL = 20, "QIWI", "В персональный кошелёк QIWI"
    YANDEX_MONEY_PERSONAL = 21, "ЮMoney", "В персональный кошелёк ЮMoney"
    QIWI_PERSONAL_BANK_CARDS = (
        22,
        "Банковские карты",
        "В персональный кошелёк QIWI",
    )
    YANDEX_MONEY_PERSONAL_APPLE_PAY = (
        23,
        "Apple Pay",
        "В персональный кошелёк ЮMoney",
    )
    YANDEX_MONEY_PERSONAL_BANK_CARDS = (
        24,
        "Банковские карты",
        "В персональный кошелёк ЮMoney",
    )
    BANK_CARDS_TINKOFF = 25, "Банковские карты", "Процессинг - Тинькофф Банк"
    YANDEX_MONEY_TINKOFF = 26, "Банковские карты", "Процессинг - НКО ЮМани"
    TINKOFF_BANK = 27, "Tinkoff Bank", "Процессинг - Тинькофф Банк"
    TINKOFF_BANK_FAST_PAYMENTS = (
        28,
        "Система быстрых платежей",
        "Процессинг - Тинькофф Банк",
    )
    TINKOFF_BANK_GOOGLE_PAY = 29, "Google Pay", "Процессинг - Тинькофф Банк"
    TINKOFF_BANK_LEGAL_ENTITY_ACCOUNT = (
        30,
        "Tinkoff Bank",
        "На Р/С Юр. лица Тинькофф Банк",
    )
    PAYPAL_USD_PERSONAL = 31, "Paypal USD", "В персональный кошелёк Paypal"
    PAYPAL_RUB_PERSONAL = 32, "Paypal RUB", "В персональный кошелёк Paypal"
    TINKOFF_BANK_IP_OOO_ACCOUNT = 33, "Tinkoff Bank", "на счёт ИП/ООО"
    TINKOFF_BUSINESS = 34, "Тинькофф Business", "На Р/С Юр. лица Тинькофф Банк"
    YU_KASSA_PERSONAL = 35, "ЮKassa", "В персональный кошелёк ЮMoney"
    BANK_CARDS_TEGRO = 36, "Банковские карты", "Процессинг - Tegro.money"
    TINKOFF_BANK_APPLE_TF = 37, "Apple TF", "На Р/С Юр. лица Тинькофф Банк"
    TINKOFF_BANK_MOBILE_PHONE_RU = (
        38,
        "Мобильный телефон РФ",
        "На Р/С Юр. лица Тинькофф Банк",
    )
    TEGRO_PAY = 39, "Tegro Pay", "На Р/С Юр. лица Тинькофф Банк"
    ROBOKASSA = 40, "RoboKassa", "На Р/С Юр. лица Тинькофф Банк"
    BANK_CARDS_TINKOFF_ACCOUNT = (
        41,
        "Банковские карты",
        "На Р/С Юр. лица Тинькофф Банк",
    )
    TONCOIN = 42, "Toncoin", "На Р/С Юр. лица Тинькофф Банк"
    BINANCE_PAY = 43, "Binance Pay", "На Р/С Юр. лица Тинькофф Банк"
    BINANCE_COIN = 44, "Binance Coin", "На Р/С Юр. лица Тинькофф Банк"
    BUSD_BNB_SMART_CHAIN = 45, "BUSD", "BNB Smart Chain (BEP20)"
    USD_COIN_BNB_SMART_CHAIN = 46, "USD Coin", "BNB Smart Chain (BEP20)"
    TETHER_USDT_BNB_SMART_CHAIN = 47, "Tether USDT", "BNB Smart Chain (BEP20)"
    TGR_BNB_SMART_CHAIN = 48, "TGR", "BNB Smart Chain (BEP20)"
    TGR_OPEN_NETWORK = 49, "TGR", "The Open Network (TON)"
    USD_COIN_ERC20 = 50, "USD Coin", "ERC20"
    TETHER_USD_TRON = 51, "Tether USD", "Tron/TRC20"

    def __new__(
        cls,
        value: int,
        title: str,
        processing: str,
    ):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj._title_ = title
        obj._processing_ = processing
        return obj

    @property
    def title(self) -> str:
        return self._title_

    @property
    def processing(self) -> str:
        return self._processing_
