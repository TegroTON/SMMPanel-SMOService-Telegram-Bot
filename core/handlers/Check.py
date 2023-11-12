import random
import time
from typing import Any, Callable, Dict, List

from aiogram import Bot, F, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import or_f
from aiogram.filters.command import Command
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Chat, Message

import database as db
from core.callback_factories.checks import (
    CheckAction,
    CheckCallbackData,
    CheckType,
    SubscriptionType,
)
from core.config import config
from core.keyboards import TextUser
from core.keyboards.checks import (
    choose_check_type_keyboard,
    create_check_subscriptions_keyboard,
    create_checks_keyboard,
    create_choose_action_keyboard,
    create_choose_subscription_type_keyboard,
    create_confirm_delete_keyboard,
    create_confirm_keyboard,
    create_delete_confirmed_keyboard,
    create_edit_check_keyboard,
    create_get_sum_keyboard,
    no_balance_keyboard,
)
from core.keyboards.utils import create_back_keyboard
from core.utils.bot import get_bot_username

check_router = Router()


class CheckState(StatesGroup):
    enter_amount = State()
    enter_quantity = State()
    enter_subscription_data = State()


@check_router.callback_query(
    or_f(
        F.data == "check",
        CheckCallbackData.filter(F.action == CheckAction.choose_type),
    )
)
async def choose_type_callback_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        TextUser.TextAddCheck,
        reply_markup=choose_check_type_keyboard,
        parse_mode=ParseMode.HTML,
    )


@check_router.callback_query(
    CheckCallbackData.filter(F.action == CheckAction.choose_action)
)
async def choose_action_callback_handler(
    callback: CallbackQuery,
    callback_data: CheckCallbackData,
):
    user_id = callback.from_user.id

    if callback_data.type == CheckType.personal:
        text = TextUser.TextPersonalCheck
        checks_count = db.get_personal_checks_count(user_id)
    else:
        text = TextUser.TextAddMultiCheck
        checks_count = db.get_multi_checks_count(user_id)

    await callback.message.edit_text(
        text,
        reply_markup=create_choose_action_keyboard(
            callback_data, checks_count
        ),
        parse_mode=ParseMode.HTML,
    )


@check_router.callback_query(
    CheckCallbackData.filter(F.action == CheckAction.get_amount)
)
async def get_sum_callback_handler(
    callback: CallbackQuery,
    callback_data: CheckCallbackData,
    state: FSMContext,
):
    user_id = callback.from_user.id
    balance = db.get_user_balance(user_id)

    if balance <= 0:
        await callback.message.edit_text(
            "Ваш баланс равен нулю. Пополните его, чтобы создавать чеки!",
            reply_markup=no_balance_keyboard,
        )
        return

    if callback_data.type == CheckType.personal:
        text = (
            "🧾<b>Персональный чек</b>\n"
            "\n"
            "Сколько рублей Вы хотите отправить пользователю с помощью \n"
            "чека?\n"
            "\n"
            f"<b>Максимум: {balance} РУБ</b>\n"
            f"Минимум: {config.CHECK_MIN_SUM} РУБ \n"
            "\n"
            "<b>Введите сумму чека в рублях:</b>"
        )
    else:
        text = (
            "🧾<b>Мульти-чек чек</b>\n"
            "\n"
            "Сколько рублей получит каждый пользователь, который\n"
            "активирует этот чек? \n"
            "\n"
            f"<b>Максимум: {balance} РУБ</b>\n"
            f"Минимум: {config.CHECK_MIN_SUM} РУБ \n"
            "\n"
            "Чем больше сумма активации, тем больше каналов/чатов\n"
            "можно добавить в условие подписки (по 1 каналу на каждые"
            f" {config.CHECK_CREDIT_PER_SUBSCRIBE} руб)\n"
            "\n"
            "<b>Введите сумму чека в рублях:</b>"
        )

    callback_data.action = (
        CheckAction.confirm
        if callback_data.type == CheckType.personal
        else CheckAction.get_quantity
    )

    await callback.message.edit_text(
        text,
        reply_markup=create_get_sum_keyboard(callback_data, balance),
        parse_mode=ParseMode.HTML,
    )

    await state.set_data(callback_data.model_dump())
    await state.set_state(CheckState.enter_amount)


@check_router.message(CheckState.enter_amount)
async def enter_amount_handler(message: Message, state: FSMContext):
    try:
        check_amount = round(float(message.text), 2)
        if check_amount < config.CHECK_MIN_SUM:
            raise ValueError
    except ValueError:
        await message.answer("Сумма должна быть положительной!")
        return

    balance = db.get_user_balance(message.from_user.id)
    if balance < check_amount:
        await message.answer(
            (
                "Введите сумму не превышающую ваш баланс!\n"
                f"Ваш баланс: {balance} руб."
            )
        )
        return

    data = await state.get_data()

    if data["type"] == CheckType.personal:
        await state.clear()
        data["amount"] = check_amount
        await process_confirm(message.answer, data)
        return

    await state.update_data({"amount": check_amount})
    await process_get_quantity(message.answer, message.from_user.id, state)


@check_router.callback_query(
    CheckCallbackData.filter(F.action == CheckAction.get_quantity)
)
async def get_quantity_callback_handler(
    callback: CallbackQuery,
    callback_data: CheckCallbackData,
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
    check_amount = data["amount"]
    balance = db.get_user_balance(user_id)

    max_quantity = round(balance / check_amount)

    await action(
        "🧾<b>Мульти-чек</b>\n"
        "\n"
        "Сколько пользователей смогут активировать этот чек?\n"
        "\n"
        f"<b>Одна активация:</b> {check_amount}\n"
        f"\n"
        f"Максимум активаций с вашим балансом: {max_quantity}\n"
        f"\n"
        f"<b>Введите количество активаций:</b>",
        reply_markup=create_back_keyboard(
            CheckCallbackData(**data).model_copy(
                update={"action": CheckAction.get_amount}
            )
        ),
        parse_mode=ParseMode.HTML,
    )

    await state.set_state(CheckState.enter_quantity)


@check_router.message(CheckState.enter_quantity)
async def enter_quantity_handler(message: Message, state: FSMContext):
    try:
        quantity = int(message.text)
        if quantity <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите положительное целое число!")
        return

    data = await state.get_data()

    balance = db.get_user_balance(message.from_user.id)
    amount = data["amount"]
    max_quantity = balance // amount
    if balance < round(amount * quantity, 2):
        await message.answer(
            (f"Вы можете указать не больше {max_quantity} активации.!\n")
        )
        return

    data["quantity"] = quantity

    await state.clear()

    await process_confirm(
        message.answer,
        data,
    )


@check_router.callback_query(
    CheckCallbackData.filter(F.action == CheckAction.confirm)
)
async def confirm_callback_handler(
    callback: CallbackQuery,
    callback_data: CheckCallbackData,
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

    if data["type"] == CheckType.personal:
        text = (
            "🧾<b>Персональный чек</b>\n"
            "\n"
            f"<b>Сумма чека:</b> {amount}\n"
            "\n"
            "🔸 <b>Пожалуйста, подтвердите корректность данных:</b>"
        )
    else:
        text = (
            "🧾<b>Мульти-чек</b>\n"
            "\n"
            f"<b>Общая сумма чека: {round(amount * quantity, 2)}</b>\n"
            "\n"
            f"<b>Внутри чека:</b> {quantity} активация(й)"
            f" по {amount} рублей\n"
            "\n"
            "<b>🔸 Пожалуйста, подтвердите корректность данных:</b>"
        )

    await action(
        text,
        reply_markup=create_confirm_keyboard(CheckCallbackData(**data)),
        parse_mode=ParseMode.HTML,
    )


@check_router.callback_query(
    CheckCallbackData.filter(F.action == CheckAction.create)
)
async def create_check_callback_handler(
    callback: CallbackQuery,
    callback_data: CheckCallbackData,
):
    user_id = callback.from_user.id

    random.seed(int(time.time()))
    while True:
        rand = int(round(random.random() * 100))
        check_number = int(user_id) * rand
        if await db.GetCheckForUser(None, None, check_number) is None:
            break

    check_type = callback_data.type
    amount = callback_data.amount
    quantity = callback_data.quantity if check_type == CheckType.multi else 1

    if amount < config.CHECK_MIN_SUM or quantity <= 0:
        await callback.message.answer(
            "Что-то пошло не так!" "Попробуйте еще раз."
        )
        return

    write_off_sum = (
        amount
        if check_type == CheckType.personal
        else round(amount * quantity, 2)
    )

    # --- Check balance is enough ---
    balance = db.get_user_balance(user_id)
    if balance < write_off_sum:
        await callback.message.edit_text(
            "Недостаточно средств, пополните баланс!",
        )
        return
    # ---

    bot_username = await get_bot_username(callback.bot)
    await db.WriteOffTheBalance(user_id, write_off_sum)
    await db.Add_History(user_id, -write_off_sum, "Создание чека")

    check_link = f"https://t.me/{bot_username}?start=check_{check_number}"
    callback_data.id = await db.AddCheck(
        user_id,
        amount,
        check_link,
        check_number,
        check_type.value,
        quantity,
    )

    await process_view_check(
        callback=callback,
        callback_data=callback_data,
        check_type=check_type.value,
        amount=amount,
        quantity=quantity,
        check_link=check_link,
        check_number=check_number,
    )


@check_router.callback_query(
    CheckCallbackData.filter(F.action == CheckAction.view_checks)
)
async def view_checks_callback_handler(
    callback: CallbackQuery,
    callback_data: CheckCallbackData,
):
    user_id = callback.from_user.id
    check_type = callback_data.type

    checks = db.get_checks_for_user(user_id, check_type.value)

    if check_type == CheckType.personal:
        text = (
            "🧾<b> Персональный чеки</b>\n"
            "\n"
            "Список Ваших персональных чеков:"
        )
    else:
        text = "🧾 <b>Мульти-чеки</b>\n" "\n" "Список Ваших мульти-чеков:"

    await callback.message.edit_text(
        text,
        reply_markup=create_checks_keyboard(callback_data, checks),
        parse_mode=ParseMode.HTML,
    )


@check_router.callback_query(
    CheckCallbackData.filter(F.action == CheckAction.view_check)
)
async def view_check_callback_handler(
    callback: CallbackQuery,
    callback_data: CheckCallbackData,
    state: FSMContext,
):
    check_data = db.get_check_by_id(callback_data.id)

    await state.clear()

    check_type = check_data[7]
    amount = check_data[2]
    quantity = check_data[3]
    check_number = check_data[5]
    check_link = check_data[4]

    await process_view_check(
        callback=callback,
        callback_data=callback_data,
        check_type=check_type,
        amount=amount,
        quantity=quantity,
        check_link=check_link,
        check_number=check_number,
    )


async def process_view_check(
    callback: CallbackQuery,
    callback_data: CheckCallbackData,
    check_type: str,
    amount: float,
    quantity: int,
    check_link: str,
    check_number: int,
):
    if CheckType(check_type) == CheckType.multi:
        text = (
            "🧾<b>Мульти-чек</b>\n"
            "\n"
            f"Сумма чека: {round(amount * quantity, 2)}\n"
            f"\n"
            f"<b>Внутри чека: {quantity} активация(й)"
            f" по {amount}рублей</b>\n"
            f"\n"
            f"Ссылка на чек:\n"
            f'<span class="tg-spoiler">{check_link}</span>'
        )
    else:
        text = (
            "🧾<b>Персональный чек</b>\n"
            "\n"
            f"<b>Сумма Чека: {amount}</b>\n"
            f"\n"
            f"<b>Ссылка на чек:</b>\n"
            f'<span class="tg-spoiler">{check_link}</span>'
        )

    await callback.message.edit_text(
        text,
        reply_markup=create_edit_check_keyboard(
            callback_data, str(check_number)
        ),
        parse_mode=ParseMode.HTML,
    )


@check_router.callback_query(
    or_f(
        CheckCallbackData.filter(F.action == CheckAction.delete),
        CheckCallbackData.filter(F.action == CheckAction.delete_subscription),
    ),
)
async def delete_handler(
    callback: CallbackQuery,
    callback_data: CheckCallbackData,
):
    if callback_data.action == CheckAction.delete:
        text = "Вы точно хотите удалить чек?"
        yes_update_data = {"action": CheckAction.delete_check_confirmed}
        no_update_data = {"action": CheckAction.view_check}
    else:
        text = "Вы точно хотите удалить подписку из чека?"
        yes_update_data = {"action": CheckAction.delete_subscription_confirmed}
        no_update_data = {"action": CheckAction.view_subscriptions}

    await callback.message.edit_text(
        text,
        reply_markup=create_confirm_delete_keyboard(
            data=callback_data,
            yes_update_data=yes_update_data,
            no_update_data=no_update_data,
        ),
    )


@check_router.callback_query(
    CheckCallbackData.filter(F.action == CheckAction.delete_check_confirmed)
)
async def delete_check_confirmed_handler(
    callback: CallbackQuery,
    callback_data: CheckCallbackData,
):
    check_id = callback_data.id
    user_id = callback.from_user.id

    check_data = db.get_check_by_user_id_and_check_id(user_id, check_id)

    if not check_data:
        await callback.message.edit_text(
            text=(
                "Что-то пошло не так!\n"
                "Такого чека не существует или вы не являетесь его владельцем!"
            ),
            reply_markup=create_back_keyboard(
                callback_data.model_copy(
                    update={"action": CheckAction.choose_action}
                )
            ),
        )
        return

    db.delete_check_by_id(check_id)
    residual_amount = round(check_data[2] * check_data[3], 2)
    await db.UpdateBalance(user_id, residual_amount)
    await db.Add_History(user_id, -residual_amount, "Удаление чека")

    await callback.message.edit_text(
        "Чек успешно удален",
        reply_markup=create_delete_confirmed_keyboard(callback_data),
    )


@check_router.callback_query(
    CheckCallbackData.filter(F.action == CheckAction.choose_subscription_type)
)
async def choose_subscription_type_callback_handler(
    callback: CallbackQuery,
    callback_data: CheckCallbackData,
    state: FSMContext,
):
    await state.clear()

    check_data = db.get_check_by_id(callback_data.id)

    subscribes_total, current_subscribes_count = get_subscribes_info(
        check_data
    )

    await callback.message.edit_text(
        text=(
            "🧾<b>Мульти-чек</b>\n"
            "\n"
            "Можно добавить обязательную подписку на группу или канал \n"
            "при активации чека. Количество групп и каналов <b>ограничено "
            "суммой одной активации</b>\n"
            "\n"
            f"Вы можете добавить до {subscribes_total} каналов в этот чек.\n"
            f"Уже добавлено: {current_subscribes_count}.\n"
            "Ваши подписки привязанные к этому мульти-чеку:"
        ),
        reply_markup=create_choose_subscription_type_keyboard(callback_data),
        parse_mode=ParseMode.HTML,
    )


@check_router.callback_query(
    CheckCallbackData.filter(F.action == CheckAction.get_chat_link)
)
async def get_chat_link_callback_handler(
    callback: CallbackQuery,
    callback_data: CheckCallbackData,
    state: FSMContext,
):
    subscription_type = callback_data.subscription_type
    if subscription_type == SubscriptionType.channel:
        text = (
            "🧾<b>Мульти-чек</b>\n"
            "\n"
            "Чтобы ограничить ваш мульти-чек каналом, перешлите сюда"
            " сообщение из канала.\n"
            "\n"
            "Я проверю, нужно ли сделать еще что-то"
        )
    elif subscription_type == SubscriptionType.public_group:
        bot_username = await get_bot_username(callback.bot)
        text = (
            "🧾<b>Мульти-чек</b>\n"
            "\n"
            "Чтобы ограничить ваш мульти-чек публичной группой, отправьте сюда"
            " инвайт-ссылку на нее.\n"
            "\n"
            f"Например https://t.me/{bot_username}"
        )
    else:
        text = (
            "🧾<b>Мульти-чек</b>\n"
            "\n"
            "Чтобы иметь возможность привязать к чеку приватную "
            "группу, Вам необходимо добавить бота в эту группу.\n"
            "\n"
            "Если этот бот не добавлен в группу, для которой вы хотите "
            "ограничить отправку чеков, пожалуйста попросите"
            "администратора добавить его.\n"
            "\n"
            "И пришлите идентификатор группы, если бот уже добавлен в ваш чат"
            " то его можно узнать отправив команду <b>/get_group_id</b> в"
            " группу\n"
        )

    await state.set_state(CheckState.enter_subscription_data)

    data = callback_data.model_dump()

    await state.set_data(data)

    callback_data.action = CheckAction.choose_subscription_type
    await callback.message.edit_text(
        text,
        reply_markup=create_back_keyboard(callback_data),
        parse_mode=ParseMode.HTML,
    )


@check_router.message(CheckState.enter_subscription_data)
async def enter_subscription_data_handler(message: Message, state: FSMContext):
    data = await state.get_data()

    check_data = db.get_check_by_id(data["id"])

    if not is_possible_to_add_subscribe(check_data):
        data["action"] = CheckAction.view_check
        await message.answer(
            text="Вы больше не можете добавлять подписки в этот чек!",
            reply_markup=create_back_keyboard(CheckCallbackData(**data)),
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
        await message.answer("Это не сообщение из канала.")
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
        await message.answer("Бот не добавлен в администраторы канала!")
        return
    # ---

    # --- Check the chat is public channel ---
    if chat.type != "channel":
        await message.answer("Это не канал!")
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

    # TODO: Add possibility to add group by invite link.
    #  Check the input is valid chat_id
    try:
        chat = await message.bot.get_chat(GroupName)
    except TelegramAPIError:
        await message.answer(
            "Такой группы не существует!\n"
            "Или эта группа является приватной.\n"
            "В этом случае выберите подписку на приватную группу."
        )
        return
    # ---

    # --- Check if chat is public group ---
    if chat.type != "supergroup":
        await message.answer("Это не публичная группа!")
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
    # TODO: Add possibility to add private group by invite link.
    #  Check the input is valid chat_id
    try:
        chat_id = int(message.text)
        chat = await bot.get_chat(chat_id)
    except ValueError:
        await message.answer("Идентификатор группы должен быть числом!")
        return
    except TelegramAPIError as e:
        print(e)
        await message.answer(
            "Такой группы не существует или бот не добавлен в группу!"
        )
        return
    # ---

    # --- Check if chat is private group ---
    if chat.type not in {"supergroup", "group"}:
        await message.answer("Это не приватная группа!")
        return
    # ---

    # --- Check if bot is group member ---
    try:
        member = await bot.get_chat_member(
            chat_id=chat.id,
            user_id=bot.id,
        )
        if member and member.status not in ["administrator", "member"]:
            raise TelegramAPIError
    except TelegramAPIError:
        await message.answer("Бот не добавлен в группу!")
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
        await message.answer("Этот канал уже добавлен в этот чек!")
        return
    # ---

    await db.UpdateChannel(check_data[5], chat.id)

    data["action"] = CheckAction.choose_subscription_type

    await message.answer(
        text="Подписка на канал/группу успешно добавлена в чек.",
        reply_markup=create_back_keyboard(CheckCallbackData(**data)),
    )


@check_router.callback_query(
    CheckCallbackData.filter(F.action == CheckAction.view_subscriptions)
)
async def view_subscriptions_callback_handler(
    callback: CallbackQuery,
    callback_data: CheckCallbackData,
):
    subscriptions = db.get_channels_for_check(callback_data.id)

    await callback.message.edit_text(
        text=(
            "🧾<b>Мульти-чек</b>\n"
            "\n"
            "Ваши подписки привязанные к этому мульти-чеку:"
        ),
        reply_markup=create_check_subscriptions_keyboard(
            data=callback_data,
            subscriptions=subscriptions,
        ),
        parse_mode=ParseMode.HTML,
    )


@check_router.callback_query(
    CheckCallbackData.filter(
        F.action == CheckAction.delete_subscription_confirmed
    )
)
async def delete_subscription_callback_handler(
    callback: CallbackQuery,
    callback_data: CheckCallbackData,
):
    await db.DeleteChannelFromCheck(callback_data.id, callback_data.chat_id)

    await callback.message.edit_text(
        "Канал был успешно удален из чека!",
        reply_markup=create_back_keyboard(
            callback_data.model_copy(update={"action": CheckAction.view_check})
        ),
    )


@check_router.callback_query(
    CheckCallbackData.filter(F.action == CheckAction.view_subscription)
)
async def view_subscription_callback_handler(
    callback: CallbackQuery,
    callback_data: CheckCallbackData,
):
    subscription = db.get_channel_by_id(callback_data.chat_id)

    name = subscription[3] if subscription[3] else f"@{subscription[2]}"

    await callback.message.edit_text(
        text=(
            "🧾<b>Подписка</b>\n"
            "\n"
            "Подписка на канал/группу привязанная к этому мульти-чеку:\n"
            f"Название канала/группы: {subscription[2]}\n"
            f"Ссылка: {name}"
        ),
        reply_markup=create_back_keyboard(
            callback_data.model_copy(
                update={"action": CheckAction.view_subscriptions}
            )
        ),
    )


@check_router.message(
    F.chat.type.in_({"group", "supergroup"}),
    Command("get_group_id"),
)
async def get_group_id_handler(message: Message, bot: Bot):
    text = f"Группа: {message.chat.title}\n" f"ID: {str(message.chat.id)}"
    await bot.send_message(message.from_user.id, text)


def get_subscribes_info(check_data: List) -> tuple[int, int]:
    """
    Calculate the total number of subscriptions and the current count of
    subscriptions based on the given check data(Result of db.GetCheckForUser).
    """
    subscribes_total = int(check_data[2] / config.CHECK_CREDIT_PER_SUBSCRIBE)
    current_subscribes_count = (
        len(check_data[8].split(",")) if check_data[8] else 0
    )
    return subscribes_total, current_subscribes_count


def is_possible_to_add_subscribe(check_data: List):
    subscribes_total, current_subscribes_count = get_subscribes_info(
        check_data,
    )

    return current_subscribes_count < subscribes_total
