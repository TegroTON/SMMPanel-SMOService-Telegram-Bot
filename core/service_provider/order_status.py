from enum import Enum


class OrderStatus(Enum):
    PENDING_PAYMENT = (
        "pending_payment",
        "Pending payment",
        "💰",
        "Без оплаты",
    )
    NEW = "new", "New", "🆕", "Новый"
    STARTING = "starting", "New", "🆕", "Запускается"
    # STARTING = 'starting', 'Starting', '🚀', "Запускается"
    IN_PROGRESS = "in_progress", "In progress", "🔄", "Выполняется"
    COMPLETED = "completed", "Completed", "✅", "Выполнен"
    PARTIAL = "partial", "Partial", "🅿️", "Частично"
    CANCELED = "canceled", "Canceled", "❌", "Отменен"

    def __new__(
        cls,
        *args,
        **kwargs,
    ):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(
        self,
        _: str,
        title: str,
        icon: str,
        russian: str,
    ) -> None:
        self.title = title
        self.icon = icon
        self.title_ru = russian

    @property
    def name_with_icon(self) -> str:
        return f"{self.icon} {self.title}"

    @property
    def name_with_icon_ru(self) -> str:
        return f"{self.icon} {self.title_ru}"

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, str):
            return __value.lower().replace(" ", "_") in {
                self.title.lower().replace(" ", "_"),
                self.title_ru.lower().replace(" ", "_"),
                self._value_.lower().replace(" ", "_"),
            }

        return super().__eq__(__value)

    @staticmethod
    def from_ru(value: str) -> "OrderStatus":
        switch_dict = {
            "ожидает_оплаты": "pending_payment",
            "новый": "new",
            "запускается": "starting",
            "выполняется": "in_progress",
            "выполнен": "completed",
            "частично": "partial",
            "отменен": "canceled",
        }
        value = value.lower().replace(" ", "_")
        value = switch_dict.get(value, value)
        return OrderStatus(value)
