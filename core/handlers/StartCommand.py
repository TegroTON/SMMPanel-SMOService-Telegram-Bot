import logging
from typing import Any, Dict

from aiogram import Bot, F, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramForbiddenError,
    TelegramNotFound,
)
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database as db
from core.config import config
from core.keyboards import Button
from core.keyboards.main_menu import get_main_menu_keyboard

logger = logging.getLogger()

start_router = Router()


@start_router.callback_query(
    F.data == "main_menu",
)
async def main_menu_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await main_menu_handler(
        message=callback.message,
        state=state,
        is_callback=True,
        user_id=callback.from_user.id,
    )


@start_router.message(F.text == "📖 Главное меню")
async def main_menu_handler(
    message: Message,
    state: FSMContext,
    is_callback: bool = False,
    user_id: int | None = None,
):
    await state.clear()

    if user_id is None:
        user_id = message.from_user.id

    text = "Выберите в меню ниже интересующий Ваc раздел:"

    if is_callback:
        reply_function = message.edit_text
    else:
        reply_function = message.answer

    is_admin = user_id == config.ADMIN_ID

    await reply_function(
        text=text,
        reply_markup=get_main_menu_keyboard(is_admin),
    )


@start_router.message(
    Command("start"),
)
async def start_command_handler(
    message: Message,
    state: FSMContext,
    bot: Bot,
):
    # TODO: Check best way to set button. This is temporary solution
    await message.answer(
        text="Устанавливаю кнопку главного меню.",
        reply_markup=Button.ReplyStartKeyboard,
    )
    # ---

    user_id = message.from_user.id

    await main_menu_handler(
        message=message,
        state=state,
        user_id=user_id,
    )

    start_command = message.text
    command = start_command[6:]

    # If user exists, activate check if command is check.
    if await db.is_user_exists(user_id):
        if "check" in command:
            await try_activate_check(
                message=message,
                bot=bot,
                start_command=start_command,
                user_id=user_id,
            )
        return
    # ---

    await db.add_user(user_id)

    if "check" in command:
        await try_activate_check(
            message=message,
            bot=bot,
            start_command=start_command,
            user_id=user_id,
            is_new_user=True,
        )

    if "ref" in command:
        try:
            affiliate_id = int(start_command[11:])
        except ValueError:
            return

        if affiliate_id == user_id:
            await message.answer(
                text=(
                    "Вы не можете регистрироваться по собственной"
                    " реферальной ссылке!"
                ),
            )
            return

        if not await db.is_user_exists(affiliate_id):
            await message.answer(
                text=(
                    "Вы попытались зарегистрироваться по некорректной"
                    " реферальной ссылке."
                    "\n"
                    "Пользователя с таким идентификатором не существует."
                ),
            )
            return

        await bind_affiliate(
            bot=bot,
            user_id=user_id,
            affiliate_id=affiliate_id,
            notify_text=(
                "По вашей реферальной ссылке зарегистрировался новый"
                " пользователь."
            ),
        )

        return

    affiliate_bot_data = db.get_bot_data_by_token(message.bot.token)
    if affiliate_bot_data:
        await bind_affiliate(
            bot=bot,
            user_id=user_id,
            affiliate_id=affiliate_bot_data["id_user"],
            notify_text="В вашем боте зарегистрировался новый пользователь.",
        )


async def try_activate_check(
    message: Message,
    bot: Bot,
    start_command: str,
    user_id: int,
    is_new_user: bool = False,
):
    try:
        check_number = int(start_command[13:])
    except ValueError:
        return

    check_data = db.get_check_by_check_number(check_number)

    # --- Check is check exist ---
    if not check_data:
        await message.answer(
            (
                f"Чека с идентификатором <b>{check_number}</b> не существует."
                "\n"
                "Возможно он был удален владельцем."
            )
        )
        return
    # ---

    if is_new_user:
        await bind_affiliate(
            bot=message.bot,
            user_id=user_id,
            affiliate_id=check_data["from_user_id"],
            notify_text="По вашему чеку зарегистрировался новый пользователь.",
        )

    if (
        check_data["UserActivate"] is not None
        and str(user_id) in check_data["UserActivate"]
    ):
        await message.answer("Вы не можете активировать чек повторно!")
        return

    if check_data["quantity"] <= 0:
        await message.answer("Этот чек уже полностью использован!")
        return

    if user_id == check_data["from_user_id"]:
        await message.answer("Вы не можете активировать свой же чек!")
        return

    if check_data["typecheck"] == "personal":
        await activate_check(
            bot=bot,
            user_id=user_id,
            check_data=check_data,
        )
        return

    subscribes_ids = (
        check_data["id_channel"].split(",") if check_data["id_channel"] else []
    )
    is_subscribed_to_all = True
    if subscribes_ids:
        for subscribe_id in subscribes_ids:
            if subscribe_id != "":
                try:
                    res = await bot.get_chat_member(int(subscribe_id), user_id)
                except TelegramAPIError:
                    await message.answer(
                        "Что-то пошло не так. Повторите попытку позже."
                    )

                is_subscribed_to_all = is_subscribed_to_all and res.status in {
                    "member",
                    "administrator",
                }

    if is_subscribed_to_all or not subscribes_ids:
        await activate_check(
            bot=bot,
            user_id=user_id,
            check_data=check_data,
        )
        return

    TextUrl = ""
    for subscribe in subscribes_ids:
        subscribe_url = await db.GetChannelUrl(subscribe)
        subscribe_title = await db.GetChannelTittle(subscribe)
        TextUrl += f'- <a href="{subscribe_url}">{subscribe_title}</a>\n'

    await bot.send_message(
        chat_id=user_id,
        text=(
            "<b>Вы не сможете активировать данный</b>\n"
            "<b>чек</b>\n"
            "\n"
            "Этот чек доступен только для подписчиков указанных ниже каналов\n"
            "Подпишитесь по указанным ниже ссылкам\n"
            f"{TextUrl}\n"
        ),
        reply_markup=await Button.SubscribeCheck(start_command),
        parse_mode=ParseMode.HTML,
    )


@start_router.callback_query(F.data.startswith("checkSubscribe_"))
async def ButtonCheckSubscribe(callback: CallbackQuery):
    await try_activate_check(
        message=callback.message,
        bot=callback.bot,
        start_command=callback.data[15:],
        user_id=callback.from_user.id,
    )


async def bind_affiliate(
    bot: Bot,
    user_id: int,
    affiliate_id: int,
    notify_text: str,
):
    db.update_user_affiliate(
        user_id=user_id,
        affiliate_id=affiliate_id,
    )
    db.update_user_balance(
        user_id=affiliate_id,
        amount=config.NEW_REFERRAL_BONUS,
    )
    await db.Add_History(
        user_id=affiliate_id,
        sum=config.NEW_REFERRAL_BONUS,
        type="Бонус - Новый реферал",
        from_user_id=user_id,
    )

    try:
        await bot.send_message(
            chat_id=affiliate_id,
            text=(
                f"{notify_text}\n"
                f"Ваш баланс пополнен на {config.NEW_REFERRAL_BONUS} руб."
            ),
        )
    except TelegramForbiddenError:
        logger.error("User with id '%s' blocked bot.", affiliate_id)
    except TelegramNotFound:
        logger.error("User with id '%s' not found.", affiliate_id)


async def activate_check(
    bot: Bot,
    user_id: int,
    check_data: Dict[str, Any],
):
    notify_message = (
        "Ваш чек был активирован!"
        if check_data["typecheck"] == "personal"
        else "Ваша мульти-чек был активирован!"
    )
    await bot.send_message(
        chat_id=check_data["from_user_id"],
        text=notify_message,
    )

    db.update_user_balance(user_id, check_data["sum"])
    await db.UpdateQuantityAndActivate(check_data["linkcheckid"], user_id)
    await db.Add_History(user_id, check_data["sum"], "Активация чека")

    await bot.send_message(
        chat_id=user_id,
        text=(
            "Вы активировали чек!\n"
            f"Ваш баланс пополнен на {check_data['sum']} руб."
        ),
    )
