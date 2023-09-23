import os
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, Message
from core.config import config
from aiogram import F, Router, Bot
from core.keyboards import TextUser, Button
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatType
import database as db
import random
from aiogram import Bot, Router

global Sum
ActivateQuantity = 1
CheckId = 0
global LinkCheckId
global RealCheckId
MaxQuantity = 0

CheckRouter = Router()

class FSMFillFrom(StatesGroup):
    GetPriceForPersonalCheck = State()
    GetPriceForMultiCheck = State()
    GetActivate = State()
    GetChannel = State()
    GetPublicGroup = State()
    GetPrivateGroup = State()


@CheckRouter.message(F.text == '🦋 Чеки')
async def Check(message: Message):
    await message.answer(TextUser.TextAddCheck, reply_markup=Button.CheckPersonOrMultiKeyboard,
                         parse_mode=ParseMode.HTML)


@CheckRouter.message(F.text == 'Назад')
async def CheckPay(message: Message, state: FSMContext):
    # Останавливаем FSM
    await state.clear()
    await message.delete()
    # Проверяем является ли пользователь админом
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        await message.answer('Вы попали в админ-панель', reply_markup=Button.ReplyAdminMainKeyboard)
    else:
        await message.answer('Выберите в меню ниже интересующий Ваc раздел:', reply_markup=Button.ReplyStartKeyboard)


@CheckRouter.callback_query(F.data == 'personal_check')
async def PersonalCheck(callback: CallbackQuery):
    print('personal')
    await callback.message.delete()
    await callback.message.answer(TextUser.TextPersonalCheck,
                                  reply_markup=await Button.GenerateCheckPersonal(callback.from_user.id),
                                  parse_mode=ParseMode.HTML)


@CheckRouter.callback_query(F.data == 'GenerateCheckForPersonal')
async def GenerateCheck(callback: CallbackQuery, state: FSMContext):
    Balance = await db.GetBalance(callback.from_user.id)
    TextGenerateCheck = '🧾<b>Персональный чек</b>\n' \
                        '\n' \
                        'Сколько рублей Вы хотите отправить пользователю с помощью \n' \
                        'чека?\n' \
                        '\n' \
                        f'<b>Максимум: {Balance[0]} РУБ</b>\n' \
                        f'Минимум: 1 РУБ \n' \
                        f'\n' \
                        f'<b>Введите сумму чека в рублях:</b>'
    await callback.message.delete()
    await callback.message.answer(TextGenerateCheck, reply_markup=Button.BackMainKeyboard,
                                  parse_mode=ParseMode.HTML)
    await state.set_state(FSMFillFrom.GetPriceForPersonalCheck)


@CheckRouter.message(FSMFillFrom.GetPriceForPersonalCheck)
async def GetPrice(message: Message, state: FSMContext):
    global Sum
    Sum = message.text
    TextForUserCreateCheck = "🧾<b>Персональный чек</b>\n" \
                             "\n" \
                             f"<b>Сумма чека:</b> {message.text}\n" \
                             f"\n" \
                             f"🔸 <b>Пожалуйста, подтвердите корректность данных:</b>"
    await message.answer(TextForUserCreateCheck, reply_markup=await Button.ConfirmCheck('personal'),
                         parse_mode=ParseMode.HTML)


@CheckRouter.callback_query(F.data.startswith('ConfirmCheck_'))
async def ConfirmCheck(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    id = callback.from_user.id
    TypeCheck = str(callback.data[13:])
    rand = round(random.random() * 100)
    LinkIdCheck = int(id) * int(rand)
    await db.WriteOffTheBalance(callback.from_user.id, int(Sum) * int(ActivateQuantity))
    CheckLink = f'https://t.me/SmmTegroTest_Bot?start={LinkIdCheck}'
    await db.AddCheck(callback.from_user.id, Sum, CheckLink, LinkIdCheck, TypeCheck, ActivateQuantity)
    if TypeCheck == 'multi':
        TextResultCheck = '🧾<b>Мульти-чек</b>\n' \
                            '\n'\
                            f'Сумма чека: {Sum}\n'\
                            f'\n'\
                            f'<b>Внутри чека: {ActivateQuantity} активация(й) по {Sum}рублей</b>\n'\
                            f'\n'\
                            f'Ссылка на чек:\n'\
                            f'<span class="tg-spoiler">{CheckLink}</span>'
    else:
        TextResultCheck = '🧾<b>Персональный чек</b>\n' \
                          '\n' \
                          f'<b>Сумма Чека: {Sum}</b>\n' \
                          f'\n' \
                          f'<b>Ссылка на чек:</b>\n' \
                          f'<span class="tg-spoiler">{CheckLink}</span>'
    await callback.message.answer(TextResultCheck, reply_markup=await Button.ForPersonalUserResultCheck(LinkIdCheck),
                                  parse_mode=ParseMode.HTML)


@CheckRouter.callback_query(F.data.startswith('DeleteCheck_'))
async def DeleteCheck(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer('Чек успешно удален', reply_markup=Button.BackMainKeyboard)
    CheckLink = str(callback.data[12:])
    Sum = await db.GetCheckForUser(None, None, CheckLink)
    Result = int(Sum[3]) * int(Sum[2])
    await db.DeleteCheck(None, None, CheckLink)
    await db.UpdateBalance(callback.from_user.id, Result)


@CheckRouter.callback_query(F.data == 'MyPersonalCheck')
async def MyPersonalCheck(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer('🧾<b>Персональный чек</b>\n'
                                  '\n'
                                  'Список Ваших персональных чеков:',
                                  reply_markup=await Button.AllUserCheck(callback.from_user.id, 'personal'),
                                  parse_mode=ParseMode.HTML)


@CheckRouter.callback_query(F.data == 'BacToPersonalCheck')
async def BacToPersonalCheck(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await Check(callback.message)


@CheckRouter.callback_query(F.data.startswith('check_'))
async def CheckStartSwitch(callback: CallbackQuery, state: FSMContext):
    CheckId = int(callback.data[6:])
    await callback.message.delete()
    Info = await db.GetCheckForUser(None, CheckId)
    print(Info)
    if Info[7] == 'personal':
        await callback.message.answer('🧾<b>Персональный чек</b>\n'
                                      '\n'
                                      f'Сумма чека: {Info[2]}\n'
                                      f'\n'
                                      f'Ссылка на чек:\n'
                                      f'<span class="tg-spoiler">{Info[4]}</span>',
                                      reply_markup=await Button.ForPersonalUserResultCheck(Info[5]),
                                      parse_mode=ParseMode.HTML)
    elif Info[7] == 'multi':
        await callback.message.answer('🧾<b>Мульти-чек</b>\n'
                                      '\n'
                                      f'Сумма чека: {Info[2]}\n'
                                      f'\n'
                                      f'<b>Внутри чека: {Info[3]} активация(й) по {Info[2]}рублей</b>\n'
                                      f'\n'
                                      f'Ссылка на чек:\n'
                                      f'<span class="tg-spoiler">{Info[4]}</span>',
                                      reply_markup=await Button.ForPersonalUserResultCheck(Info[5]),
                                      parse_mode=ParseMode.HTML)


@CheckRouter.callback_query(F.data == 'MultiCheck')
async def MultiCheck(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(TextUser.TextAddMultiCheck,
                                  reply_markup=await Button.GenerateCheckMulti(callback.from_user.id),
                                  parse_mode=ParseMode.HTML)


@CheckRouter.callback_query(F.data == 'GenerateCheckMulti')
async def GenerateCheckMulti(callback: CallbackQuery, state: FSMContext):
    Balance = await db.GetBalance(callback.from_user.id)
    TextGenerateCheck = '🧾<b>Мульти-чек чек</b>\n' \
                        '\n' \
                        'Сколько рублей получит каждый пользователь, который\n' \
                        'активирует этот чек? \n' \
                        '\n' \
                        f'<b>Максимум: {Balance[0]} РУБ</b>\n' \
                        f'Минимум: 10 РУБ \n' \
                        f'\n' \
                        f'Чем больше сумма активации, тем больше каналов/чатов\n' \
                        f'можно добавить в условие подписки (по 1 каналу на каждые 10 руб)\n' \
                        f'\n' \
                        f'<b>Введите сумму чека в рублях:</b>'
    await callback.message.delete()
    await callback.message.answer(TextGenerateCheck, reply_markup=Button.BackMainKeyboard,
                                  parse_mode=ParseMode.HTML)
    await state.set_state(FSMFillFrom.GetPriceForMultiCheck)


@CheckRouter.message(FSMFillFrom.GetPriceForMultiCheck)
async def GetPriceForMultiCheck(message: Message, state: FSMContext):
    global Sum, MaxQuantity
    Balance = await db.GetBalance(message.from_user.id)
    Sum = message.text
    if int(Sum) >= 10:
        if Balance[0] >= int(Sum):
            Balance = await db.GetBalance(message.from_user.id)
            MaxQuantity = int(int(Balance[0]) / int(Sum))
            TextForUserCreateCheck = "🧾<b>Мульти-чек</b>\n" \
                                     "\n" \
                                     "Сколько пользователей смогут активировать этот чек?\n" \
                                     "\n" \
                                     f"<b>Одна активация:</b> {message.text}\n" \
                                     f"\n" \
                                     f"Максимум активаций с вашим балансом: {MaxQuantity}\n" \
                                     f"\n" \
                                     f"<b>Введите количество активаций:</b>"
            await message.answer(TextForUserCreateCheck, reply_markup=Button.BackMainKeyboard,
                                 parse_mode=ParseMode.HTML)
            await state.set_state(FSMFillFrom.GetActivate)
        else:
            await message.answer('Сумма вашего баланса меньше чем сумма чека')
    else:
        await message.answer('Введите стоимость одного чека больше 10')


@CheckRouter.message(FSMFillFrom.GetActivate)
async def GetActivate(message: Message, state: FSMContext):
    global ActivateQuantity
    if int(message.text) <= MaxQuantity:
        ActivateQuantity = int(message.text)
        TextForMultiCheck = "🧾<b>Мульти-чек</b>\n" \
                            "\n" \
                            f"<b>Сумма чека: {Sum}</b>\n" \
                            f"\n" \
                            f"<b>Внутри чека:</b> {ActivateQuantity} активация(й) по {Sum} рублей\n" \
                            f"\n" \
                            f"<b>🔸 Пожалуйста, подтвердите корректность данных:</b>"
        await message.answer(TextForMultiCheck, reply_markup=await Button.ConfirmCheck('multi'), parse_mode=ParseMode.HTML)
    else:
        await message.answer('Вы указали кол-во активаций невозможное с вашим балансом')

@CheckRouter.callback_query(F.data.startswith('Add_Subscribe_'))
async def AddSubscribe(call: CallbackQuery):
    global CheckId
    await call.message.delete()
    CheckId = int(call.data[14:])
    await call.message.answer('🧾<b>Мульти-чек</b>\n'
                              '\n'
                              'Если вы хотите ограничить активацию чека подписчиками\n'
                              'определенной группы или канала, выберите тип ниже.\n'
                              '\n',
                              reply_markup=await Button.AddChannel(CheckId),
                              parse_mode=ParseMode.HTML)


@CheckRouter.callback_query(F.data.startswith('CheckChannel_'))
async def CheckChannel(call: CallbackQuery):
    await call.message.delete()
    checkid = int(call.data[13:])
    Check = await db.GetCheckForUser(None, None, checkid)
    global RealCheckId
    RealCheckId = Check[0]
    await call.message.answer('Ваши подписки привязанные к этому мульти-чеку',
                              reply_markup=await Button.DeleteChannel(RealCheckId))


@CheckRouter.callback_query(F.data == 'MyMultiCheck')
async def MyPersonalCheck(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer('🧾<b>Мульти-чеки</b>\n'
                                  '\n'
                                  'Список Ваших мульти-чеков.\n'
                                  'Выберите интересующий чек для редактирования или удаления.\n'
                                  '\n'
                                  '<b>Список Ваших мультичеков:</b>',
                                  reply_markup=await Button.AllUserCheck(
                                      callback.from_user.id, 'multi'),
                                  parse_mode=ParseMode.HTML)


@CheckRouter.callback_query(F.data.startswith('Channel_'))
async def Channel(callback: CallbackQuery, state: FSMContext):
    global LinkCheckId
    LinkCheckId = int(callback.data[8:])
    print(CheckId)
    await callback.message.delete()
    await state.set_state(FSMFillFrom.GetChannel)
    await callback.message.answer('🧾<b>Мульти-чек</b>\n'
                                  '\n'
                                  'Чтобы ограничить ваш мульти-чек каналом, перешлите сюда \n'
                                  'сообщение из канала.\n'
                                  '\n'
                                  'Я проверю, нужно ли сделать еще что-то',
                                  reply_markup=Button.BackCheckKeyboard,
                                  parse_mode=ParseMode.HTML)


@CheckRouter.message(FSMFillFrom.GetChannel)
async def GetUrlChannel(message: Message, state: FSMContext, bot: Bot):
    Id = int(message.forward_from_chat.id)
    await message.delete()
    Check = await db.GetCheckForUser(None, None, LinkCheckId)
    print(LinkCheckId)
    global RealCheckId
    RealCheckId = Check[0]
    Chan = int(Check[2]) / 10
    Name = await bot.get_chat(Id)
    await db.AddChanel(Id, Name.title, Name.invite_link)
    await db.UpdateChannel(CheckId, Id)
    try:
        await message.answer('🧾<b>Мульти-чек</b>\n'
                             '\n'
                             'Можно добавить обязательную подписку на группу или канал \n'
                             'при активации чека. Количество групп и каналов <b>ограничено </b>\n'
                             '<b>суммой одной активации\n</b>'
                             '\n'
                             f'Вы можете добавить до {Chan} каналов на вашу сумму чека.\n',
                             reply_markup=await Button.DeleteChannel(RealCheckId),
                             parse_mode=ParseMode.HTML)
    except:
        await message.answer('🧾<b>Мульти-чек</b>\n'
                             '\n'
                             'Чтобы ограничить ваш мульти-чек каналом, перешлите сюда \n'
                             'сообщение из канала.\n'
                             '\n'
                             '<b>Я проверю, нужно ли сделать еще что-то</b>\n'
                             '🔺 Бот не добавлен в канал, пожалуйста \n'
                             'попросите администратора добавить. Они могут\n'
                             'выключить все разрешения у бота, они ему не нужны.',
                             parse_mode=ParseMode.HTML)


@CheckRouter.callback_query(F.data.startswith('PublicGroup_'))
async def PublicGroup(callback: CallbackQuery, state: FSMContext):
    global LinkCheckId
    LinkCheckId = int(callback.data[12:])
    await callback.message.delete()
    await callback.message.answer('🧾<b>Мульти-чек</b>\n'
                                  '\n'
                                  'Чтобы ограничить ваш мульти-чек публичной группой, отправьте сюда \n'
                                  'инвайт-ссылку на нее.\n'
                                  '\n'
                                  'Например https://t.me/SmmTegroTest_Bot',
                                  reply_markup=Button.BackCheckKeyboard,
                                  parse_mode=ParseMode.HTML)
    await state.set_state(FSMFillFrom.GetPublicGroup)


@CheckRouter.message(FSMFillFrom.GetPublicGroup)
async def GetPublicGroup(message: Message, state: FSMContext, bot: Bot):
    GroupName = '@' + str(message.text[13:])
    Chat_id = await bot.get_chat(GroupName)
    print(message.text)
    await db.AddChanel(Chat_id.id, Chat_id.title, message.text)
    await db.UpdateChannel(LinkCheckId, Chat_id.id)
    Check = await db.GetCheckForUser(None, None, CheckId)
    global RealCheckId
    RealCheckId = Check[0]
    Chan = int(Check[2]) / 10
    await message.answer('🧾<b>Мульти-чек</b>\n'
                         '\n'
                         'Можно добавить обязательную подписку на группу или канал \n'
                         'при активации чека. Количество групп и каналов <b>ограничено </b>\n'
                         '<b>суммой одной активации\n</b>'
                         '\n'
                         f'Вы можете добавить до {Chan} каналов на вашу сумму чека.\n',
                         reply_markup=await Button.DeleteChannel(RealCheckId),
                         parse_mode=ParseMode.HTML)


@CheckRouter.callback_query(F.data.startswith('PrivateGroup_'))
async def PrivateGroup(callback: CallbackQuery, state: FSMContext):
    global LinkCheckId
    LinkCheckId = int(callback.data[13:])
    await callback.message.delete()
    await callback.message.answer('🧾<b>Мульти-чек</b>\n'
                                  '\n'
                                  'Что бы иметь возможность привязать к чеку приватную \n'
                                  'группу, Вам необходимо добавить бота в эту группу.\n'
                                  '\n'
                                  'Если этот бот не добавлен в группу, для которой вы хотите \n'
                                  'ограничить отправку чеков, пожалуйста попросите \n'
                                  'администратора добавить его.\n'
                                  '\n'
                                  'И пришлите идентификатор группы, если бот уже добавлен'
                                  'в ваш чат то его можно узнать отправив <b>+groupID</b> в группе\n',
                                  reply_markup=Button.BackCheckKeyboard,
                                  parse_mode=ParseMode.HTML)
    await state.set_state(FSMFillFrom.GetPrivateGroup)


@CheckRouter.message(FSMFillFrom.GetPrivateGroup)
async def GetPrivateGroup(message: Message, state: FSMContext, bot: Bot):
    ChannelId = int(message.text)
    Chat_id = await bot.get_chat(ChannelId)
    await db.AddChanel(Chat_id.id, Chat_id.title, Chat_id.invite_link)
    await db.UpdateChannel(LinkCheckId, Chat_id.id)
    Check = await db.GetCheckForUser(None, None, CheckId)
    global RealCheckId
    RealCheckId = Check[0]
    Chan = int(int(Check[2]) / 10)
    await message.answer('🧾<b>Мульти-чек</b>\n'
                         '\n'
                         'Можно добавить обязательную подписку на группу или канал \n'
                         'при активации чека. Количество групп и каналов <b>ограничено </b>\n'
                         '<b>суммой одной активации\n</b>'
                         '\n'
                         f'Вы можете добавить до {Chan} каналов на вашу сумму чека.\n',
                         reply_markup=await Button.DeleteChannel(RealCheckId),
                         parse_mode=ParseMode.HTML)


@CheckRouter.message(F.text == '+groupID' and F.chat.type == 'group')
async def GetIdGroup(message: Message, bot: Bot):
    text = str(message.chat.id)
    await bot.send_message(message.chat.id, text)


@CheckRouter.callback_query(F.data.startswith('deletechannel_'))
async def DeleteChannel(callback: CallbackQuery, state: FSMContext):
    ChannelId = int(callback.data[14:])
    await callback.message.delete()
    await db.DeleteChannelFromCheck(RealCheckId, ChannelId)
    await callback.message.answer('Канал был удален', reply_markup=Button.BackCheckKeyboard)