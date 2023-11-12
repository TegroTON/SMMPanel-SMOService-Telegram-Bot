from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message

import database as db
from core.config import config
from core.keyboards import Button

# Создаю глобальные переменные
InfoProduct = ""
NameParentCategory = ""

AddOrRemoveCategoryRouter = Router()


# Создаю машину состояний или FSM
class FSMFillFrom(StatesGroup):
    fill_AddCategory = State()
    fill_AddSubCategory = State()
    fill_AnswerAddSubCategory = State()
    fill_AddProduct = State()
    fill_default = StateFilter(default_state)
    fill_AddToRemove = State()
    fill_InfoProduct = State()


# Обрабатываю команду по добавление и удалению категории и подкатегории
@AddOrRemoveCategoryRouter.message(
    F.text == "Добавление и удаление категории и подкатегории"
)
async def CreateCategory(message: Message, bot: Bot):
    """
    Проверяем что бы id пользователя являлся id админа
    или пишем что не такой команды для защиты
    доступа к админ-панели
    """
    if message.from_user.id == config.ADMIN_ID:
        await message.answer(
            "Выберете удалить или добавить категорию",
            reply_markup=Button.AddOrRemoveCategoryKeyboard,
        )

    else:
        await message.answer("Я не знаю такой команды")


# Обрабатываем нажатие на кнопку добавления категории
@AddOrRemoveCategoryRouter.callback_query(F.data == "AddCategory")
async def AddCategory(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите название категории")
    # Используем FSM для обработки название категории
    await state.set_state(FSMFillFrom.fill_AddCategory)
    await callback.message.delete()


# Обрабатываем нажатие на кнопку назад
@AddOrRemoveCategoryRouter.callback_query(F.data == "BackToMainMenuAdmin")
async def BackToMainMenu(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Хорошо", reply_markup=Button.ReplyAdminMainKeyboard
    )
    await callback.message.delete()


# Обрабатываем нажатие на кнопку удаления
@AddOrRemoveCategoryRouter.callback_query(
    F.data == "RemoveCategorySubCategory"
)
async def RemoveCategorySubCategory(
    callback: CallbackQuery, state: FSMContext
):
    # Выводи клавиатуру действий
    await callback.message.answer(
        "Выберите удалить категорию или подкатегорию",
        reply_markup=Button.RemoveCategoryOrSubCategory,
    )


# Обрабатываем нажатие на удаление категории
@AddOrRemoveCategoryRouter.callback_query(F.data == "RemoveCategory")
async def RemoveCategory(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Выберите какую категорию удалить ?",
        reply_markup=await Button.CategoryMarkup("Delete"),
    )


# Обрабатываем нажатие на удаление подкатегории
@AddOrRemoveCategoryRouter.callback_query(F.data == "RemoveSubCategory")
async def RemoveSubCategory(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Выберите какую подкатегорию удалить ?",
        reply_markup=await Button.SubCategoryMarkup("Delete"),
    )


# Используем функция проверки данных callback для обработки удаления категории
@AddOrRemoveCategoryRouter.callback_query(F.data.startswith("Delete_category"))
async def Delete_Category(call):
    await call.message.answer("Вы выбрали категорию")
    # Получаем id категории для отправки в базу данных для удаления
    CategoryId = int(call.data[16:])
    # Обращаемся к базе данных для удаления
    res = await db.DeleteCategory(CategoryId)
    await call.message.answer(res)
    await call.message.answer(
        "Хотите добавить или удалить еще ?",
        reply_markup=Button.AddOrRemoveCategoryKeyboard,
    )
    await call.message.delete()


# Используем FSM для добавления категории
@AddOrRemoveCategoryRouter.message(StateFilter(FSMFillFrom.fill_AddCategory))
async def StateAddCategory(message: Message, state: FSMContext):
    # Проверка на админа
    if message.from_user.id == config.ADMIN_ID:
        # Обращаемся к базе данных для добавления в нее категории
        res = await db.AddCategory(message.text, config.Service)
        # Глобальная переменная для получения id родительской категории при
        #  добавлении подкатегории
        global NameParentCategory
        NameParentCategory = message.text
        await message.answer(res)
        await message.answer(
            "Хотите ли вы добавить подкатегории для этой категории ?",
            reply_markup=Button.AddSubCategoryKeyboard,
        )
    else:
        await message.answer("Я не знаю такой команды")


# Обрабатываем нажатие на кнопку добавления подкатегории
@AddOrRemoveCategoryRouter.callback_query(F.data == "AddSubCategory")
async def AddSubCategory(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите название подкатегории")
    # Используем FSM
    await state.set_state(FSMFillFrom.fill_AddSubCategory)
    await callback.message.delete()


# Если человек отказался добавлять подкатегорию
@AddOrRemoveCategoryRouter.callback_query(F.data == "NoSubCategory")
async def NoSubCategory(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Хорошо", reply_markup=Button.ReplyAdminMainKeyboard
    )
    await callback.message.delete()
    await state.clear()


# Используем FSM для добавления подкатегории
@AddOrRemoveCategoryRouter.message(
    StateFilter(FSMFillFrom.fill_AddSubCategory)
)
async def StateAddSubCategory(message: Message, state: FSMContext):
    # Проверка на админ
    if message.from_user.id == config.ADMIN_ID:
        # Получаем id родительской категории
        ParentID = await db.GetIdParentCategory(NameParentCategory)
        # Добавляем подкатегорию в бд
        res = await db.AddCategory(message.text, ParentID)
        await message.answer(res)
        await message.answer(
            "Хотите добавить еще ?", reply_markup=Button.AddSubCategoryKeyboard
        )
    else:
        await message.answer("Я не знаю такой команды")
