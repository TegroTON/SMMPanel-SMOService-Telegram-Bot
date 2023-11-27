from .texts import ButtonText, MessageText


class TextManager:
    bot_id: int
    button: ButtonText
    message: MessageText

    def __init__(
        self,
        # bot_id: int,
    ) -> None:
        self.button = ButtonText()
        self.message = MessageText()
        # self.bot_id = bot_id
