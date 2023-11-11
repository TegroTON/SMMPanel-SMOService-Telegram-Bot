import asyncio

from aiogram import F, Router
from aiogram.types import Message

from core.service_provider.manager import provider_manager
from core.service_provider.provider import ServiceParseError

ParsingRouter = Router()


@ParsingRouter.message(F.text == "Обновить парсинг")
async def SendAll(
    message: Message,
):
    tasks = []
    for provider in provider_manager.get_active_services_list():
        tasks.append(provider.parse_services())

    messages = []
    for coroutine in asyncio.as_completed(tasks):
        try:
            service_name = await coroutine
            messages.append(
                f"Парсинг сервиса <b>'{service_name}'</b> прошел успешно.\n"
            )
        except ServiceParseError as error:
            messages.append(
                f"Парсинг сервиса <b>'{error.service_name}'</b> не удался.\n"
                f"Причина: {error.cause}!\n"
            )

    results = "\n".join(messages)

    await message.answer(
        text=f"<b>Результаты парсинга</b>\n\n{results}",
    )
