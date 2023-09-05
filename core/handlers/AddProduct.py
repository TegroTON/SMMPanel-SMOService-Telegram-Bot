import os
from aiogram.filters import StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, Message, \
    CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.command import Command
from aiogram import F
from aiogram.fsm.state import default_state
from core.keyboards import Button
from core.config import config
import database as db


ParentId = 0
NameParentCategory = ''


class FSMFillFrom(StatesGroup):
    fill_AddCategory = State()
    fill_AddSubCategory = State()
    fill_AnswerAddSubCategory = State()
    fill_AddProduct = State()
    fill_default = StateFilter(default_state)
    fill_AddToRemove = State()
    fill_InfoProduct = State()
    fill_InfoDeleteProduct = State()


# кнопка добавления товара
@config.dp.message(F.Text == 'Товары', StateFilter(default_state))
async def CreateCategory(message: Message, state: FSMContext):
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        await message.answer('Выберите добавить в категорию, подкатегорию или удалить товар', reply_markup=Button.AddProductToCategoryOrSubCategory.as_markup())
    else:
        await message.answer('Я не знаю такой команды')


@config.dp.message(StateFilter(FSMFillFrom.fill_InfoProduct))
async def InfoProduct(message: Message, state: FSMContext):
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        InfoProduct = message.text.split(',')
        ProductName = str(InfoProduct[0])
        MinOrder = int(InfoProduct[1])
        MaxOrder = int(InfoProduct[2])
        Price = float(InfoProduct[3])
        res = await db.AddProduct(ParentId, ProductName, MinOrder, MaxOrder, Price)
        await message.answer(res)
        await state.clear()

    else:
        await message.answer('Я не знаю такой команды')


@config.dp.callback_query(F.Text == 'DeleteProduct')
async def DeleteProduct(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('Выберите категорию или подкатегорию', reply_markup=await Button.CategoryAndSubCategory('DeleteProduct'))


@config.dp.callback_query(F.Text == 'AddToCategory')
async def AddToCategory(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('Выберите категорию', reply_markup=await Button.CategoryMarkup('add'))


@config.dp.callback_query(F.Text == 'AddToSubCategory')
async def AddToSubCategory(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('Выберите подкатегорию', reply_markup=await Button.SubCategoryMarkup('add'))


@config.dp.callback_query(F.Text.startswith == 'add_category')
async def Add_Category(call, state: FSMContext):
    global ParentId
    ParentId = int(call.data[13:])
    await call.message.answer('Введите название продукта, минимальное и максимальное количество и цену')
    await state.set_state(FSMFillFrom.fill_InfoProduct)


@config.dp.callback_query(F.Text.startswith == 'DeleteProduct_category')
async def DeleteProduct_Category(call):
    await call.message.answer('Вы выбрали категорию или подкатегорию')
    ParentId = int(call.data[23:])
    await call.message.answer('Выберите товар', reply_markup=await Button.CheckProduct('delete', ParentId))


@config.dp.callback_query(F.Text.startswith == 'delete_product')
async def Delete_Product(callback: CallbackQuery, state: FSMContext):
    ProductId = int(callback.data[15:])
    print(ProductId)
    res = await db.DeleteProduct(ProductId)
    await callback.message.answer(res)
