import os
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
import database as db
from aiogram import Bot
from main import main_router
from core.keyboards import Button
from aiogram import Bot, Router
from aiogram.types import Message, CallbackQuery
from aiogram import F

StartRouter = Router()


# Обработка команды старт
@StartRouter.message(Command('start'))
async def Start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        await message.answer('Вы попали в админ-панель', reply_markup=Button.ReplyAdminMainKeyboard)
    else:
        await message.answer('Выберите в меню ниже интересующий Ваc раздел:', reply_markup=Button.ReplyStartKeyboard)
    # Если до этого пользователя нет в бд, то добавляем ему баланс
    if not await db.CheckUserInBalance(message.from_user.id):
        await db.UserBalance(message.from_user.id)
    # Если пользователя нет в бд по рефералам, то происходит операция добавления
    if not await db.UserExists(message.from_user.id):
        start_command = message.text
        # Получаем id пользователя
        referral_id = str(start_command[7:])
        # Если id не равен пустой строке
        if str(referral_id) != '':
            # Не равен пользователя который отправил ссылку
            if str(referral_id) != str(message.from_user.id):
                # Добавляем в таблицу рефералов
                Check = await db.GetCheckForUser(None, referral_id)
                print(Check)
                if Check is not None:
                    CheckReferral = await db.GetReferral(referral_id)
                    if CheckReferral is not None:
                        await db.AddUserReferral(message.from_user.id, referral_id)
                        try:
                            await bot.send_message(referral_id,
                                                   'По вашей ссылке зарегистрировался новый пользователь')
                        except:
                            pass
            else:
                await db.AddUserReferral(message.from_user.id)
                await bot.send_message(message.from_user.id,
                                       'Нельзя регистрироваться по собственной реферальной ссылке')
        else:
            await db.AddUserReferral(message.from_user.id)
    start_command = message.text
    await ActivateCheck(message, bot, start_command)
    # Вывод главный интерфейс


async def ActivateCheck(message: Message, bot: Bot, start_command):
    IdCheckLink = str(start_command[7:])
    print(IdCheckLink)
    status = ''
    if IdCheckLink != '':
        CheckData = await db.GetCheckForUser(None, None, IdCheckLink)
        if CheckData[6] is not None and str(message.from_user.id) in CheckData[6]:
            await message.answer('Вы не можете активировать чек повторно')
        else:
            if CheckData[3] > 0:
                if CheckData[7] == 'personal':
                    if int(message.from_user.id) != int(CheckData[1]):
                        await db.UpdateBalance(message.from_user.id, CheckData[2])
                        await bot.send_message(CheckData[1], 'Ваш чек был активирован')
                        await db.UpdateQuantityAndActivate(CheckData[5], message.from_user.id)
                    else:
                        await message.answer('Вы не можете активировать свой же чек')
                else:
                    if int(message.from_user.id) != int(CheckData[1]):
                        Chan = CheckData[8]
                        if Chan is not None:
                            print('я тут')
                            Channels = Chan.split(',')
                            for channel in Channels:
                                print(message.from_user.id)
                                if channel != '':
                                    res = await bot.get_chat_member(int(channel), message.from_user.id)
                                    print(res)
                                    if res.status == 'left':
                                        status = 'left'
                                    elif res.status == 'member':
                                        status = 'member'
                                    elif res.status == 'administrator':
                                        status = 'administrator'
                                    print(status)
                        if status == 'left':
                            Channels = Chan.split(',')
                            TextUrl = ''
                            for channel in Channels:
                                ChannelUrl = await db.GetChannelUrl(channel)
                                ChannelTittle = await db.GetChannelTittle(channel)
                                TextUrl += f'- <a href="{ChannelUrl}">{ChannelTittle}</a>\n'
                            TextMessage = '<b>Вы не сможете активировать данный</b>\n' \
                                          '<b>чек</b>\n' \
                                          '\n' \
                                          'Этот чек доступен только для подписчиков указанных ниже каналов\n' \
                                          'Подпишитесь по указанным ниже ссылкам\n' \
                                          f'{TextUrl}\n'
                            await bot.send_message(message.from_user.id, TextMessage, reply_markup=await Button.SubscribeCheck(start_command), parse_mode=ParseMode.HTML)
                        elif status == 'member' or Chan is None or status == 'administrator':
                            if int(await db.GetUserCheckActivate(message.from_user.id)) == 0 \
                                    and message.from_user.id != await db.GetReferral(CheckData[1]):
                                await db.AddUserReferral(message.from_user.id, CheckData[1])
                                await db.UpdateCheckActivate(message.from_user.id)
                            else:
                                await db.UpdateCheckActivate(message.from_user.id)
                            await db.UpdateBalance(message.from_user.id, CheckData[2])
                            await bot.send_message(CheckData[1], 'Ваш чек был активирован')
                            await db.UpdateQuantityAndActivate(CheckData[5], message.from_user.id)
                            await bot.send_message(message.from_user.id, 'Вы активировали чек')
                            print('активировала')
                        print(status)
                    else:
                        await message.answer('Вы не можете активировать свой же чек')
            else:
                await message.answer('Этот чек уже полностью использован')


@StartRouter.callback_query(F.data.startswith('checkSubscribe_'))
async def ButtonCheckSubscribe(callback: CallbackQuery, bot: Bot):
    print('привет')
    StartCommand = str(callback.data[15:])
    print(StartCommand)
    await ActivateCheck(callback, bot, StartCommand)