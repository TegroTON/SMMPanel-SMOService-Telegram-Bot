import logging
from typing import Any, Dict

from aiogram import Bot, F, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNotFound,
)
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from core.callback_factories.cheques import CheckSubscribesCallbackData
from core.keyboards.cheques import create_check_subscribes_keyboard
from core.utils.bot import get_bot_id_by_token

import database as db
from core.config import config
from core.keyboards.main_menu import (
    create_main_menu_button_reply_keyboard,
    get_main_menu_keyboard,
)
from core.text_manager import text_manager as tm

logger = logging.getLogger(__name__)

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


@start_router.message(F.text == tm.button.main_menu())
async def main_menu_handler(
    message: Message,
    state: FSMContext,
    is_callback: bool = False,
    user_id: int | None = None,
):
    await state.set_state(None)

    if user_id is None:
        user_id = message.from_user.id

    if is_callback:
        reply_function = message.edit_text
    else:
        reply_function = message.answer

    is_admin = user_id == config.ADMIN_ID

    await reply_function(
        text=tm.message.main_menu(),
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
    await message.answer(
        text=tm.message.init(),
        reply_markup=create_main_menu_button_reply_keyboard(),
    )

    user_id = message.from_user.id

    await main_menu_handler(
        message=message,
        state=state,
        user_id=user_id,
    )

    start_command = message.text
    command = start_command[7:]
    cheque_number = None

    if "check" in command:
        try:
            cheque_number = command[6:]
        except ValueError:
            await message.answer(
                text=tm.message.cheque_activate_wrong_number().format(
                    cheque_number=cheque_number
                ),
            )

    bot_id = get_bot_id_by_token(token=message.bot.token)

    # If user exists, activate check if command is check.
    if await db.is_user_exists(user_id):
        db.update_user_bot(user_id, bot_id)
        if cheque_number:
            await try_activate_check(
                message=message,
                bot=bot,
                cheque_number=cheque_number,
                user_id=user_id,
            )
        return
    # ---

    await db.add_user(user_id, bot_id)

    if cheque_number and await try_activate_check(
        message=message,
        bot=bot,
        cheque_number=cheque_number,
        user_id=user_id,
        is_new_user=True,
    ):
        return

    elif "ref" in command:
        try:
            affiliate_id = int(start_command[11:])
        except ValueError:
            return

        if affiliate_id == user_id:
            await message.answer(
                text=tm.message.referrals_try_own_link(),
            )
            return

        if not await db.is_user_exists(affiliate_id):
            await message.answer(
                text=tm.message.referrals_incorrect_link(),
            )
            return

        await bind_affiliate(
            bot=bot,
            user_id=user_id,
            affiliate_id=affiliate_id,
            notify_text=tm.message.referrals_bind_link(),
        )

        return

    affiliate_bot_data = db.get_bot_data_by_token(message.bot.token)
    if affiliate_bot_data:
        await bind_affiliate(
            bot=bot,
            user_id=user_id,
            affiliate_id=affiliate_bot_data["id_user"],
            notify_text=tm.message.referrals_bind_bot(),
        )


async def try_activate_check(
    message: Message,
    bot: Bot,
    cheque_number: int,
    user_id: int,
    is_new_user: bool = False,
) -> bool:
    cheque_data = db.get_check_by_check_number(cheque_number)

    # --- Check is check exist ---
    if not cheque_data:
        await message.answer(
            text=tm.message.cheque_activate_wrong_number().format(
                cheque_number=cheque_number
            ),
        )
        return False
    # ---

    if is_new_user:
        await bind_affiliate(
            bot=message.bot,
            user_id=user_id,
            affiliate_id=cheque_data["from_user_id"],
            notify_text=tm.message.referrals_bind_cheque(),
        )

    if (
        cheque_data["UserActivate"] is not None
        and str(user_id) in cheque_data["UserActivate"]
    ):
        await message.answer(text=tm.message.cheque_try_reactivation())
        return False

    if cheque_data["quantity"] <= 0:
        await message.answer(tm.message.cheque_fully_activated())
        return False

    if user_id == cheque_data["from_user_id"]:
        await message.answer(tm.message.cheque_try_own_cheque())
        return False

    if cheque_data["typecheck"] == "personal":
        await activate_check(
            bot=bot,
            user_id=user_id,
            cheque_data=cheque_data,
        )
        return True

    subscribes_ids = (
        cheque_data["id_channel"].split(",")
        if cheque_data["id_channel"]
        else []
    )
    is_subscribed_to_all = True
    if subscribes_ids:
        for subscribe_id in subscribes_ids:
            if subscribe_id != "":
                try:
                    res = await bot.get_chat_member(
                        int(subscribe_id),
                        user_id,
                    )
                except TelegramAPIError:
                    await message.answer(
                        text=tm.message.try_later(),
                    )

                is_subscribed_to_all = is_subscribed_to_all and res.status in {
                    "member",
                    "administrator",
                }

    if is_subscribed_to_all or not subscribes_ids:
        await activate_check(
            bot=bot,
            user_id=user_id,
            cheque_data=cheque_data,
        )
        return True

    subscribes_list = ""
    for subscribe in subscribes_ids:
        subscribe_url = await db.GetChannelUrl(subscribe)
        subscribe_title = await db.GetChannelTitle(subscribe)
        subscribes_list += (
            f'🔸 <a href="{subscribe_url}">{subscribe_title}</a>\n'
        )

    await bot.send_message(
        chat_id=user_id,
        text=tm.message.cheque_needs_subscriptions().format(
            subscribes_list=subscribes_list
        ),
        reply_markup=create_check_subscribes_keyboard(
            cheque_number=cheque_number
        ),
        parse_mode=ParseMode.HTML,
    )

    return False


@start_router.callback_query(
    CheckSubscribesCallbackData.filter(),
)
async def check_subscribes_callback_handler(
    callback: CallbackQuery,
    callback_data: CheckSubscribesCallbackData,
):
    await try_activate_check(
        message=callback.message,
        bot=callback.bot,
        cheque_number=callback_data.cheque_number,
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
            text=tm.message.referrals_get_bonus().format(
                cause_description=notify_text,
                amount=config.NEW_REFERRAL_BONUS,
            ),
        )
    except TelegramForbiddenError:
        logger.error("User with id '%s' blocked bot.", affiliate_id)
    except TelegramNotFound:
        logger.error("User with id '%s' not found.", affiliate_id)
    except TelegramBadRequest:
        logger.error("Chat with id '%s' not found.", affiliate_id)


async def activate_check(
    bot: Bot,
    user_id: int,
    cheque_data: Dict[str, Any],
):
    notify_message = tm.message.cheque_your_cheque_activated().format(
        cheque_type="чек"
        if cheque_data["typecheck"] == "personal"
        else "мульти-чек"
    )
    await bot.send_message(
        chat_id=cheque_data["from_user_id"],
        text=notify_message,
    )

    db.update_user_balance(user_id, cheque_data["sum"])
    await db.UpdateQuantityAndActivate(cheque_data["linkcheckid"], user_id)
    await db.Add_History(user_id, cheque_data["sum"], "Активация чека")

    await bot.send_message(
        chat_id=user_id,
        text=tm.message.cheque_successfully_activated().format(
            amount=cheque_data["sum"]
        ),
    )
