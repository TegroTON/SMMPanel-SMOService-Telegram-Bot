from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

import database as db
from core.config import config
from core.keyboards.referral import referral_keyboard
from core.utils.bot import get_bot_username

referral_router = Router()


@referral_router.callback_query(F.data == "earn")
async def ReferralLinkCommand(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    percents_iter = iter(config.REFERRAL_REPLENISH_BONUS_PERCENTS)

    referrals = db.get_referrals(user_id)

    bot_username = await get_bot_username(callback.bot)

    total_bonus_amount = db.get_total_bonus_amount(user_id)

    text = (
        "<b>🤝 Партнерская программа</b>\n"
        "\n"
        "🏆 Вознаграждения по реферальной (партнерской) \n"
        "программе разделены на два уровня:\n"
        "├  За пользователей которые присоединились по Вашей ссылке "
        "- рефералы 1 уровня\n"
        "└  За пользователей которые присоединились по ссылкам Ваших"
        " рефералов - рефералы 2 уровня"
        "\n"
        "🤑 Сколько можно заработать?\n"
        f"├  За реферала 1 уровня: {next(percents_iter)}%\n"
        f"└  За реферала 2 уровня: {next(percents_iter)}%\n"
        "\n"
        "🥇 Статистика:\n"
        f"├  Всего заработано: {total_bonus_amount}\n"
        # f"├  Доступно к выводу: {total_bonus_amount}\n"
        f"└  Лично приглашенных: {len(referrals)}\n"
        "\n"
        "🎁 Бонус за регистрацию:\n"
        "└  За каждого пользователя который активировал бот по вашей"
        f" реферальной ссылке вы так же получаете {config.NEW_REFERRAL_BONUS}"
        " рублей.\n"
        "\n"
        "⤵️ Ваши ссылки:\n"
        f"└ https://t.me/{bot_username}?start=ref_{user_id}\n"
    )

    await callback.message.edit_text(
        text,
        reply_markup=referral_keyboard,
    )
