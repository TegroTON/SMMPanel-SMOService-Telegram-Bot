import random
import time
from typing import Any, Callable, Dict, List

from aiogram import F, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import or_f
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Chat, Message

import database as db
from core.callback_factories.cheques import (
    ChequeAction,
    ChequeCallbackData,
    ChequeType,
    SubscriptionType,
)
from core.config import config
from core.keyboards.cheques import (
    create_check_subscriptions_keyboard,
    create_checks_keyboard,
    create_cheque_choose_action_keyboard,
    create_choose_subscription_type_keyboard,
    create_confirm_delete_keyboard,
    create_confirm_keyboard,
    create_delete_confirmed_keyboard,
    create_edit_cheque_keyboard,
    create_get_sum_keyboard,
    create_no_balance_keyboard,
    create_get_quantity_keyboard,
)
from core.keyboards.utils import create_back_keyboard
from core.utils.bot import get_bot_username
from core.text_manager import text_manager as tm

check_router = Router()


class CheckState(StatesGroup):
    enter_amount = State()
    enter_quantity = State()
    enter_subscription_data = State()


@check_router.callback_query(
    or_f(
        F.data == "cheque",
        ChequeCallbackData.filter(F.action == ChequeAction.choose_action),
    )
)
async def choose_action_callback_handler(
    callback: CallbackQuery,
):
    cheques_count = db.get_personal_checks_count(callback.from_user.id)
    multi_cheques_count = db.get_multi_checks_count(callback.from_user.id)
    await callback.message.edit_text(
        text=tm.message.cheques(),
        reply_markup=create_cheque_choose_action_keyboard(
            cheques_count=cheques_count,
            multi_cheques_count=multi_cheques_count,
        ),
        parse_mode=ParseMode.HTML,
    )


@check_router.callback_query(
    ChequeCallbackData.filter(F.action == ChequeAction.get_amount)
)
async def get_sum_callback_handler(
    callback: CallbackQuery,
    callback_data: ChequeCallbackData,
    state: FSMContext,
):
    user_id = callback.from_user.id
    balance = db.get_user_balance(user_id)

    if balance <= 0:
        await callback.message.edit_text(
            text=tm.message.cheques_low_balance(),
            reply_markup=create_no_balance_keyboard(),
        )
        return

    if callback_data.type == ChequeType.personal:
        text = tm.message.cheques_personal_get_amount()
    else:
        text = tm.message.cheques_multi_get_amount().format(
            check_min_sum=round(config.CHEQUE_MIN_SUM, 2),
            sum_for_four=round(config.CHEQUE_MIN_SUM * 1.5, 2),
            sum_for_five=round(config.CHEQUE_MIN_SUM * 2, 2),
        )

    callback_data.action = (
        ChequeAction.confirm
        if callback_data.type == ChequeType.personal
        else ChequeAction.get_quantity
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_get_sum_keyboard(callback_data, balance),
    )

    await state.set_data(callback_data.model_dump())
    await state.set_state(CheckState.enter_amount)


@check_router.message(CheckState.enter_amount)
async def enter_amount_handler(message: Message, state: FSMContext):
    try:
        check_amount = round(float(message.text), 2)
        if check_amount < config.CHEQUE_MIN_SUM:
            raise ValueError
    except ValueError:
        await message.answer(tm.message.cheques_amount_must_be_positive())
        return

    balance = db.get_user_balance(message.from_user.id)
    if balance < check_amount:
        await message.answer(
            tm.message.cheques_wrong_amount().format(balance=balance)
        )
        return

    data = await state.get_data()

    if data["type"] == ChequeType.personal:
        await state.clear()
        data["amount"] = check_amount
        await process_confirm(message.answer, data)
        return

    await state.update_data({"amount": check_amount})
    await process_get_quantity(message.answer, message.from_user.id, state)


@check_router.callback_query(
    ChequeCallbackData.filter(F.action == ChequeAction.get_quantity)
)
async def get_quantity_callback_handler(
    callback: CallbackQuery,
    callback_data: ChequeCallbackData,
    state: FSMContext,
):
    await state.set_data(callback_data.model_dump())

    await process_get_quantity(
        callback.message.edit_text,
        callback.from_user.id,
        state,
    )


async def process_get_quantity(
    action: Callable,
    user_id: int,
    state: FSMContext,
):
    data = await state.get_data()
    cheque_amount = data["amount"]
    balance = db.get_user_balance(user_id)

    max_quantity = int(balance // cheque_amount)

    await action(
        text=tm.message.cheques_get_quantity().format(
            cheque_amount=cheque_amount,
            max_quantity=max_quantity,
        ),
        reply_markup=create_get_quantity_keyboard(
            data=ChequeCallbackData(**data),
            max_quantity=max_quantity,
        ),
    )

    await state.set_state(CheckState.enter_quantity)


@check_router.message(CheckState.enter_quantity)
async def enter_quantity_handler(message: Message, state: FSMContext):
    try:
        quantity = int(message.text)
        if quantity <= 0:
            raise ValueError
    except ValueError:
        await message.answer(tm.message.cheques_enter_positive_quantity())
        return

    data = await state.get_data()

    balance = db.get_user_balance(message.from_user.id)
    amount = data["amount"]
    max_quantity = int(balance // amount)
    if quantity > max_quantity:
        await message.answer(
            text=tm.message.cheques_wrong_quantity().format(
                max_quantity=max_quantity,
            )
        )
        return

    data["quantity"] = quantity

    await state.clear()

    await process_confirm(
        message.answer,
        data,
    )


@check_router.callback_query(
    ChequeCallbackData.filter(F.action == ChequeAction.confirm)
)
async def confirm_callback_handler(
    callback: CallbackQuery,
    callback_data: ChequeCallbackData,
    state: FSMContext,
):
    await state.clear()

    await process_confirm(
        callback.message.edit_text,
        callback_data.model_dump(),
    )


async def process_confirm(
    action: Callable,
    data: Dict[str, Any],
):
    amount = data["amount"]
    quantity = data["quantity"]

    if data["type"] == ChequeType.personal:
        text = tm.message.cheques_confirm_personal().format(
            amount=amount,
        )
    else:
        text = tm.message.cheques_confirm_multi().format(
            total_amount=round(amount * quantity, config.BALANCE_PRECISION),
            quantity=quantity,
            amount=amount,
        )

    await action(
        text,
        reply_markup=create_confirm_keyboard(ChequeCallbackData(**data)),
        parse_mode=ParseMode.HTML,
    )


@check_router.callback_query(
    ChequeCallbackData.filter(F.action == ChequeAction.create)
)
async def create_cheque_callback_handler(
    callback: CallbackQuery,
    callback_data: ChequeCallbackData,
):
    user_id = callback.from_user.id

    random.seed(int(time.time()))
    while True:
        rand = int(round(random.random() * 100))
        check_number = int(user_id) * rand
        if await db.GetCheckForUser(None, None, check_number) is None:
            break

    cheque_type = callback_data.type
    amount = callback_data.amount
    quantity = callback_data.quantity if cheque_type == ChequeType.multi else 1

    if amount < config.CHEQUE_MIN_SUM or quantity <= 0:
        await callback.message.answer(text=tm.message.try_later())
        return

    write_off_sum = (
        amount
        if cheque_type == ChequeType.personal
        else round(amount * quantity, 2)
    )

    # --- Check balance is enough ---
    balance = db.get_user_balance(user_id)
    if balance < write_off_sum:
        await callback.message.edit_text(
            text=tm.message.cheques_insufficient_funds(),
            reply_markup=create_no_balance_keyboard(),
        )
        return
    # ---

    bot_username = await get_bot_username(callback.bot)
    await db.WriteOffTheBalance(user_id, write_off_sum)
    await db.Add_History(user_id, -write_off_sum, "Создание чека")

    check_link = f"https://t.me/{bot_username}?start=check_{check_number}"
    callback_data.id = await db.AddCheck(
        user_id=user_id,
        price=amount,
        url=check_link,
        linkcheckid=check_number,
        TypeCheck=cheque_type.value,
        quantity=quantity,
        total_quantity=quantity,
    )

    await process_view_check(
        callback=callback,
        callback_data=callback_data,
        cheque_type=cheque_type.value,
        amount=amount,
        quantity=quantity,
        cheque_link=check_link,
        cheque_number=check_number,
        total_quantity=quantity,
    )


@check_router.callback_query(
    ChequeCallbackData.filter(F.action == ChequeAction.view_checks)
)
async def view_checks_callback_handler(
    callback: CallbackQuery,
    callback_data: ChequeCallbackData,
):
    user_id = callback.from_user.id
    check_type = callback_data.type

    checks = db.get_checks_for_user(user_id, check_type.value)

    if check_type == ChequeType.personal:
        text = tm.message.cheques_list_personal()
    else:
        text = tm.message.cheques_list_multi()

    await callback.message.edit_text(
        text=text,
        reply_markup=create_checks_keyboard(callback_data, checks),
        parse_mode=ParseMode.HTML,
    )


@check_router.callback_query(
    ChequeCallbackData.filter(F.action == ChequeAction.view_check)
)
async def view_check_callback_handler(
    callback: CallbackQuery,
    callback_data: ChequeCallbackData,
    state: FSMContext,
):
    check_data = db.get_check_by_id(callback_data.id)

    await state.clear()

    check_type = check_data[7]
    amount = check_data[2]
    quantity = check_data[3]
    check_number = check_data[5]
    check_link = check_data[4]
    total_quantity = check_data[9]

    await process_view_check(
        callback=callback,
        callback_data=callback_data,
        cheque_type=check_type,
        amount=amount,
        quantity=quantity,
        cheque_link=check_link,
        cheque_number=check_number,
        total_quantity=total_quantity,
    )


async def process_view_check(
    callback: CallbackQuery,
    callback_data: ChequeCallbackData,
    cheque_type: str,
    amount: float,
    quantity: int,
    cheque_link: str,
    cheque_number: int,
    total_quantity: int,
):
    if ChequeType(cheque_type) == ChequeType.multi:
        status = (
            "Полностью активирован"
            if quantity == 0
            else "Частично активирован"
            if quantity != total_quantity
            else "Не активирован"
        )
        text = tm.message.cheques_info_multi().format(
            total_amount=round(
                amount * total_quantity, config.BALANCE_PRECISION
            ),
            status=status,
            quantity=quantity,
            total_quantity=total_quantity,
            amount=amount,
            cheque_link=cheque_link,
        )
    else:
        status = (
            "Активирован" if quantity != total_quantity else "Не активирован"
        )
        text = tm.message.cheques_info_personal().format(
            amount=amount,
            status=status,
            cheque_link=cheque_link,
        )

    await callback.message.edit_text(
        text,
        reply_markup=create_edit_cheque_keyboard(
            data=callback_data,
            link=str(cheque_number),
            is_fully_activated=quantity == 0,
        ),
        parse_mode=ParseMode.HTML,
    )


@check_router.callback_query(
    or_f(
        ChequeCallbackData.filter(F.action == ChequeAction.delete),
        ChequeCallbackData.filter(
            F.action == ChequeAction.delete_subscription
        ),
    ),
)
async def delete_handler(
    callback: CallbackQuery,
    callback_data: ChequeCallbackData,
):
    if callback_data.action == ChequeAction.delete:
        text = tm.message.cheque_delete_confirm()
        yes_update_data = {"action": ChequeAction.delete_check_confirmed}
        no_update_data = {"action": ChequeAction.view_check}
    else:
        text = tm.message.cheque_delete_subscription_confirm()
        yes_update_data = {
            "action": ChequeAction.delete_subscription_confirmed
        }
        no_update_data = {"action": ChequeAction.view_subscriptions}

    await callback.message.edit_text(
        text,
        reply_markup=create_confirm_delete_keyboard(
            data=callback_data,
            yes_update_data=yes_update_data,
            no_update_data=no_update_data,
        ),
    )


@check_router.callback_query(
    ChequeCallbackData.filter(F.action == ChequeAction.delete_check_confirmed)
)
async def delete_check_confirmed_handler(
    callback: CallbackQuery,
    callback_data: ChequeCallbackData,
):
    check_id = callback_data.id
    user_id = callback.from_user.id

    check_data = db.get_check_by_user_id_and_check_id(user_id, check_id)

    if not check_data:
        await callback.message.edit_text(
            text=tm.message.cheque_delete_error(),
            reply_markup=create_back_keyboard(
                callback_data.model_copy(
                    update={"action": ChequeAction.choose_action}
                )
            ),
        )
        return

    db.delete_check_by_id(check_id)
    residual_amount = round(check_data[2] * check_data[3], 2)
    await db.UpdateBalance(user_id, residual_amount)
    await db.Add_History(user_id, residual_amount, "Удаление чека")

    await callback.message.edit_text(
        text=tm.message.cheque_successfully_deleted(),
        reply_markup=create_delete_confirmed_keyboard(callback_data),
    )


@check_router.callback_query(
    ChequeCallbackData.filter(
        F.action == ChequeAction.choose_subscription_type
    )
)
async def add_subscription_callback_handler(
    callback: CallbackQuery,
    callback_data: ChequeCallbackData,
    state: FSMContext,
):
    await state.clear()

    await callback.message.edit_text(
        text=tm.message.cheque_add_subscribe(),
        reply_markup=create_choose_subscription_type_keyboard(
            data=callback_data,
        ),
    )


@check_router.callback_query(
    ChequeCallbackData.filter(F.action == ChequeAction.get_chat_link)
)
async def get_chat_link_callback_handler(
    callback: CallbackQuery,
    callback_data: ChequeCallbackData,
    state: FSMContext,
):
    subscription_type = callback_data.subscription_type
    if subscription_type == SubscriptionType.channel:
        text = tm.message.cheque_add_channel()
    elif subscription_type == SubscriptionType.public_group:
        bot_username = await get_bot_username(callback.bot)
        text = tm.message.cheque_add_group().format(
            bot_username=bot_username,
        )
    else:
        text = tm.message.cheque_add_private_group()

    await state.set_state(CheckState.enter_subscription_data)

    data = callback_data.model_dump()

    await state.set_data(data)

    callback_data.action = ChequeAction.choose_subscription_type
    await callback.message.edit_text(
        text,
        reply_markup=create_back_keyboard(callback_data),
    )


@check_router.message(CheckState.enter_subscription_data)
async def enter_subscription_data_handler(message: Message, state: FSMContext):
    data = await state.get_data()

    check_data = db.get_check_by_id(data["id"])

    if not is_possible_to_add_subscribe(check_data):
        data["action"] = ChequeAction.view_check
        await message.answer(
            text=tm.message.cheque_no_more_subscribes(),
            reply_markup=create_back_keyboard(ChequeCallbackData(**data)),
        )
        return

    subscription_type = data["subscription_type"]

    if subscription_type == SubscriptionType.channel:
        await process_add_channel(
            message=message,
            data=data,
            check_data=check_data,
        )
    elif subscription_type == SubscriptionType.public_group:
        await process_add_public_group(
            message=message,
            data=data,
            check_data=check_data,
        )
    else:
        await process_add_private_group(
            message=message,
            data=data,
            check_data=check_data,
        )


async def process_add_channel(
    message: Message,
    data: Dict[str, Any],
    check_data: List[Any],
):
    # --- Check if message is from channel ---
    if not message.forward_from_chat:
        await message.answer(
            text=tm.message.cheque_message_not_from_channel(),
        )
        return
    # ---

    channel_id = message.forward_from_chat.id

    bot = message.bot

    # --- Check if bot is admin in channel ---
    try:
        chat = await bot.get_chat(channel_id)
        chat_administrators = await bot.get_chat_administrators(
            chat_id=channel_id
        )
        if message.bot.id not in [
            member.user.id for member in chat_administrators
        ]:
            raise TelegramAPIError
    except TelegramAPIError:
        await message.answer(
            text=tm.message.cheque_bot_not_channel_admin(),
        )
        return
    # ---

    # --- Check the chat is public channel ---
    if chat.type != "channel":
        await message.answer(
            text=tm.message.cheque_not_a_channel(),
        )
        return
    # ---

    if not await db.GetChannelUrl(channel_id):
        if not chat.username:
            invite_link = await bot.export_chat_invite_link(chat.id)
        else:
            invite_link = f"https://t.me/{chat.username}"

        await db.AddChanel(
            chat.id,
            chat.title,
            Url=invite_link,
        )

    await process_add_subscribe_to_check(
        message=message,
        chat=chat,
        data=data,
        check_data=check_data,
    )


async def process_add_public_group(
    message: Message,
    data: Dict[str, Any],
    check_data: List[Any],
):
    GroupName = "@" + str(message.text.split("/")[-1])

    #  Check the input is valid chat_id
    is_chat = True
    try:
        chat = await message.bot.get_chat(GroupName)
    except TelegramAPIError:
        is_chat = False
    # ---

    # --- Check if chat is public group ---
    if not is_chat or chat.type != "supergroup":
        await message.answer(
            text=tm.message.cheque_not_a_public_group(),
        )
        return
    # ---

    await db.AddChanel(chat.id, chat.title, Url=message.text)

    await process_add_subscribe_to_check(
        message=message,
        chat=chat,
        data=data,
        check_data=check_data,
    )


async def process_add_private_group(
    message: Message,
    data: Dict[str, Any],
    check_data: List[Any],
):
    bot = message.bot

    try:
        chat_id = int(message.text)
        chat = await bot.get_chat(chat_id)
    except ValueError:
        await message.answer(
            text=tm.message.cheque_wrong_group_id(),
        )
        return
    except TelegramAPIError:
        await message.answer(
            text=tm.message.cheque_bot_not_in_group(),
        )
        return
    # ---

    # --- Check if chat is private group ---
    if chat.type not in {"supergroup", "group"}:
        await message.answer(
            text=tm.message.cheque_group_is_not_private(),
        )
        return
    # ---

    # --- Check if bot is group member ---
    try:
        member = await bot.get_chat_member(
            chat_id=chat.id,
            user_id=bot.id,
        )
        if (
            member.status not in {"administrator"}
            or not member.can_invite_users
        ):
            raise Exception("Bot is not group admin!")

    except Exception:
        await message.answer(
            text=tm.message.cheque_bot_is_not_group_admin(),
        )
        return

    # ---

    if not await db.GetChannelUrl(chat_id):
        invite_link = await bot.export_chat_invite_link(chat.id)
        await db.AddChanel(
            chat.id,
            chat.title,
            Url=invite_link,
        )

    await process_add_subscribe_to_check(
        message=message,
        chat=chat,
        data=data,
        check_data=check_data,
    )


async def process_add_subscribe_to_check(
    message: Message,
    chat: Chat,
    data: Dict[str, Any],
    check_data: List[Any],
):
    # --- Check is channel already added ---
    if check_data[8] and str(chat.id) in check_data[8].split(","):
        await message.answer(
            text=tm.message.cheque_subscribe_already_added(),
        )
        return
    # ---

    if not is_possible_to_add_subscribe(check_data):
        await message.answer(
            text=tm.message.cheque_no_more_subscribes(),
        )

    await db.UpdateChannel(check_data[5], chat.id)

    data["action"] = ChequeAction.view_subscriptions

    await message.answer(
        text=tm.message.cheque_subscribe_added(),
        reply_markup=create_back_keyboard(
            data=ChequeCallbackData(**data),
            text=tm.button.subscribes(),
        ),
    )


@check_router.callback_query(
    ChequeCallbackData.filter(F.action == ChequeAction.view_subscriptions)
)
async def view_subscriptions_callback_handler(
    callback: CallbackQuery,
    callback_data: ChequeCallbackData,
):
    check_data = db.get_check_by_id(callback_data.id)

    subscribes_total, current_subscribes_count = get_subscribes_info(
        check_data
    )

    text = tm.message.cheque_subscribes_info().format(
        amount_per_subscribe=config.CHEQUE_CREDIT_PER_SUBSCRIBE,
    )

    if subscribes_total > 0:
        text += (
            "Этот чек поддерживает до <b>{subscribes_total}</b> подписок.\n"
            "\n"
            "Количество подписок в этом чеке: <b>{current_subscribes_count} / {subscribes_total}</b>\n"  # noqa
            "\n"
        ).format(
            subscribes_total=subscribes_total,
            current_subscribes_count=current_subscribes_count,
        )
        if subscribes_total <= current_subscribes_count:
            text += (
                "<b>🔸Вы не можете добавить больше подписок в этот чек.</b>\n"
            )
    else:
        text += (
            "<b>🔸 Сумма одной активации меньше {amount_per_subscribe} руб!</b>\n"  # noqa
            "\n"
            "<b>🔸 Вы не можете добавлять подписки в этот чек.</b>\n"
        ).format(amount_per_subscribe=config.CHEQUE_CREDIT_PER_SUBSCRIBE)

    subscriptions = db.get_channels_for_check(callback_data.id)

    await callback.message.edit_text(
        text=text,
        reply_markup=create_check_subscriptions_keyboard(
            data=callback_data,
            subscriptions=subscriptions,
            subscribes_left=subscribes_total - current_subscribes_count,
        ),
    )


@check_router.callback_query(
    ChequeCallbackData.filter(
        F.action == ChequeAction.delete_subscription_confirmed
    )
)
async def delete_subscription_callback_handler(
    callback: CallbackQuery,
    callback_data: ChequeCallbackData,
):
    await db.DeleteChannelFromCheck(callback_data.id, callback_data.chat_id)

    await callback.message.edit_text(
        text=tm.message.cheque_subscribe_deleted(),
        reply_markup=create_back_keyboard(
            callback_data.model_copy(
                update={"action": ChequeAction.view_check}
            )
        ),
    )


@check_router.callback_query(
    ChequeCallbackData.filter(F.action == ChequeAction.view_subscription)
)
async def view_subscription_callback_handler(
    callback: CallbackQuery,
    callback_data: ChequeCallbackData,
):
    subscription = db.get_channel_by_id(callback_data.chat_id)

    name = subscription[3] if subscription[3] else f"@{subscription[2]}"

    await callback.message.edit_text(
        text=tm.message.cheque_subscribe().format(
            title=subscription[2], link=name
        ),
        reply_markup=create_back_keyboard(
            callback_data.model_copy(
                update={"action": ChequeAction.view_subscriptions}
            )
        ),
    )


def get_subscribes_info(check_data: List) -> tuple[int, int]:
    """
    Calculate the total number of subscriptions and the current count of
    subscriptions based on the given check data(Result of db.GetCheckForUser).
    """
    subscribes_total = int(
        min(
            config.CHEQUE_DEFAULT_SUBSCRIBES
            + (check_data[2] - 0.1) // config.CHEQUE_CREDIT_PER_SUBSCRIBE,
            config.CHEQUE_MAX_SUBSCRIBES,
        )
    )
    current_subscribes_count = (
        len(check_data[8].split(",")) if check_data[8] else 0
    )
    return subscribes_total, current_subscribes_count


def is_possible_to_add_subscribe(check_data: List):
    subscribes_total, current_subscribes_count = get_subscribes_info(
        check_data,
    )

    return current_subscribes_count < subscribes_total
