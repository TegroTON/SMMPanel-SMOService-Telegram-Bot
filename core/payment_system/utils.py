from aiogram import Bot

import database as db
from core.config import config


def save_paylink(
    user_id: int,
    order_id: str,
    payment_gateway: str,
    bot_token: str,
    amount: float,
) -> int:
    bot_id = db.get_bot_id_by_token(bot_token)
    if not bot_id:
        bot_id = -1

    paylink_id = db.add_paylink(
        user_id=user_id,
        order_id=order_id,
        payment_system=payment_gateway,
        bot_id=bot_id,
        amount=amount,
    )

    return paylink_id


async def replenish_affiliate_balance(
    user_id: int,
    amount: float,
    bot: Bot,
):
    bonus_iter = iter(config.REFERRAL_REPLENISH_BONUS_PERCENTS)
    affiliate_id = db.get_affiliate_id(user_id)
    referral_level = 1
    while affiliate_id and (bonus_percent := next(bonus_iter, None)):
        affiliate_bonus = bonus_percent / 100 * amount
        db.update_user_balance(
            user_id=affiliate_id,
            amount=affiliate_bonus,
        )
        await db.Add_History(
            user_id=affiliate_id,
            sum=affiliate_bonus,
            type="Бонус - Заказ услуги рефералом",
            from_user_id=user_id,
        )
        await bot.send_message(
            chat_id=affiliate_id,
            text=(
                f"Ваш реферал {referral_level} заказал услугу.\n"
                f"Ваш бонус: {affiliate_bonus} руб."
            ),
        )
        referral_level += 1
        affiliate_id = db.get_affiliate_id(affiliate_id)


async def refund_user_balance(
    user_id: int,
    amount: float,
    order_id: int,
    is_partial: bool = False,
):
    db.update_user_balance(
        user_id=user_id,
        amount=amount,
    )

    if is_partial:
        operation_type = "Частичное выполнение заказа"
    else:
        operation_type = "Отмена заказа"

    await db.Add_History(
        user_id=user_id,
        sum=amount,
        type=operation_type,
        order_id=order_id,
    )
