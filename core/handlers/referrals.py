from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

import database as db
from core.config import config
from core.keyboards.referral import create_referral_keyboard
from core.text_manager import text_manager as tm
from core.utils.bot import get_bot_username

referral_router = Router()


@referral_router.callback_query(F.data == "earn")
async def referrals_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await state.set_state(None)

    user_id = callback.from_user.id

    percents_iter = iter(config.REFERRAL_REPLENISH_BONUS_PERCENTS)

    referrals = db.get_referrals(user_id)

    bot_username = await get_bot_username(callback.bot)

    total_bonus_amount = db.get_total_bonus_amount(user_id)

    text = tm.message.referrals().format(
        level_one_percents=next(percents_iter),
        level_two_percents=next(percents_iter),
        total_bonus_amount=total_bonus_amount,
        referrals_count=len(referrals),
        bonus_amount=config.NEW_REFERRAL_BONUS,
        bot_username=bot_username,
        user_id=user_id,
    )

    await callback.message.edit_text(
        text,
        reply_markup=create_referral_keyboard(),
    )
