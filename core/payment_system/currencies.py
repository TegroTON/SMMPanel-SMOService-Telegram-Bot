from enum import StrEnum


class Currency(StrEnum):
    RUB = "RUB", "Российский рубль"
    EUR = "EUR", "Евро"
    USD = "USD", "Доллар США"
    AUD = "AUD", "Австралийский доллар"
    AZN = "AZN", "Азербайджанский манат"
    AMD = "AMD", "Армянский драм"
    BYN = "BYN", "Белорусский рубль"
    BGN = "BGN", "Болгарский лев"
    BRL = "BRL", "Бразильский реал"
    HUF = "HUF", "Венгерский форинт"
    KRW = "KRW", "Вон Республики Корея"
    HKD = "HKD", "Гонконгский доллар"
    DKK = "DKK", "Датская крона"
    INR = "INR", "Индийский рупий"
    KZT = "KZT", "Казахстанский тенге"
    CAD = "CAD", "Канадский доллар"
    KGS = "KGS", "Киргизский сом"
    CNY = "CNY", "Китайский юань"
    MDL = "MDL", "Молдавский лей"
    TMT = "TMT", "Новый туркменский манат"
    NOK = "NOK", "Норвежский крон"
    PLN = "PLN", "Польский злотый"
    RON = "RON", "Румынский лей"
    SGD = "SGD", "Сингапурский доллар"
    TJS = "TJS", "Таджикский сомони"
    TRY = "TRY", "Турецкая лира"
    UZS = "UZS", "Узбекский сум"
    UAH = "UAH", "Украинская гривна"
    GBP = "GBP", "Фунт стерлингов Соединенного королевства"
    CZK = "CZK", "Чешская крона"
    SEK = "SEK", "Шведская крона"
    CHF = "CHF", "Швейцарский франк"
    ZAR = "ZAR", "Южноафриканский рэнд"
    JPY = "JPY", "Японская иена"

    def __new__(
        cls,
        value: str,
        title: str,
    ):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._title_ = title
        return obj

    @property
    def title(self) -> str:
        return self._title_
