from aiogram import Bot
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.callback_factories.my_bots import MyBotAction, MyBotCallbackData
from core.keyboards.utils import create_back_keyboard

import database as db
from core.keyboards.main_menu import to_main_menu_button
from core.service_provider.manager import provider_manager

StartKeyboard = [
    [
        KeyboardButton(text="📖 Главное меню"),
    ]
]
ReplyStartKeyboard = ReplyKeyboardMarkup(
    keyboard=StartKeyboard, resize_keyboard=True
)


AdminMainKeyboard = [
    [
        KeyboardButton(text="📖 Главное меню"),
    ],
]
ReplyAdminMainKeyboard = ReplyKeyboardMarkup(
    keyboard=AdminMainKeyboard, resize_keyboard=True
)


AdminPanelKeyboard = [
    [
        KeyboardButton(text="📖 Главное меню"),
    ],
    [
        KeyboardButton(text="Добавление и удаление категории и подкатегории"),
    ],
    [
        KeyboardButton(text="Обновить парсинг"),
    ],
    [
        KeyboardButton(text="Список заказов и статусы"),
    ],
    [
        KeyboardButton(text="Рассылка"),
    ],
    # [
    # KeyboardButton(text='Редактирование сообщений')
    # ],
    [
        KeyboardButton(text="Выбрать сервис для создания заказа"),
    ],
]
ReplyAdminPanelKeyboard = ReplyKeyboardMarkup(
    keyboard=AdminPanelKeyboard,
    resize_keyboard=True,
    one_time_keyboard=True,
)


BackMainButton = [[KeyboardButton(text="Админ-панель")]]
BackMainKeyboard = ReplyKeyboardMarkup(
    keyboard=BackMainButton, resize_keyboard=True
)


GetService = [
    [InlineKeyboardButton(text="Вместе", callback_data="All_service")],
    [InlineKeyboardButton(text="SmmPanel", callback_data="SmmPanelService")],
    [InlineKeyboardButton(text="SmoService", callback_data="SmoService")],
]
GetServiceKeyboard = InlineKeyboardMarkup(inline_keyboard=GetService)


AddOrRemoveCategoryButton = [
    [InlineKeyboardButton(text="Добавить", callback_data="AddCategory")],
    [
        InlineKeyboardButton(
            text="Удалить", callback_data="RemoveCategorySubCategory"
        )
    ],
    [
        InlineKeyboardButton(
            text="⬅️Назад", callback_data="BackToMainMenuAdmin"
        )
    ],
]
AddOrRemoveCategoryKeyboard = InlineKeyboardMarkup(
    inline_keyboard=AddOrRemoveCategoryButton
)


RemoveCategoryOrSubCategoryButton = [
    [
        InlineKeyboardButton(
            text="удалить категорию", callback_data="RemoveCategory"
        ),
        InlineKeyboardButton(
            text="удалить подкатегорию", callback_data="RemoveSubCategory"
        ),
    ]
]
RemoveCategoryOrSubCategory = InlineKeyboardMarkup(
    inline_keyboard=RemoveCategoryOrSubCategoryButton
)


AddSubCategoryButton = [
    [InlineKeyboardButton(text="Да", callback_data="AddSubCategory")],
    [InlineKeyboardButton(text="Нет", callback_data="NoSubCategory")],
    [InlineKeyboardButton(text="Назад", callback_data="BackToMainMenuAdmin")],
]
AddSubCategoryKeyboard = InlineKeyboardMarkup(
    inline_keyboard=AddSubCategoryButton
)


AddProductToCategoryOrSubCategoryButton = [
    [
        InlineKeyboardButton(
            text="в подкатегорию", callback_data="AddToSubCategory"
        )
    ],
    [InlineKeyboardButton(text="в категорию", callback_data="AddToCategory")],
    [
        InlineKeyboardButton(
            text="удалить товар", callback_data="DeleteProduct"
        )
    ],
    [InlineKeyboardButton(text="Назад", callback_data="BackToMainMenuAdmin")],
]
AddProductToCategoryOrSubCategory = InlineKeyboardMarkup(
    inline_keyboard=AddProductToCategoryOrSubCategoryButton
)


Balance = [
    [
        InlineKeyboardButton(
            text="📥Пополнить", callback_data="replenish_balance"
        ),
    ],
    [
        InlineKeyboardButton(
            text="📨История операций", callback_data="history_balance"
        ),
        InlineKeyboardButton(
            text="📋 История заказов", callback_data="history_order"
        ),
    ],
]
BalanceKeyboard = InlineKeyboardMarkup(inline_keyboard=Balance)


BalanceSum = [
    [
        InlineKeyboardButton(text="250", callback_data="SumReplenish_250"),
        InlineKeyboardButton(text="500", callback_data="SumReplenish_500"),
        InlineKeyboardButton(text="2500", callback_data="SumReplenish_2500"),
    ],
    [
        InlineKeyboardButton(text="500", callback_data="SumReplenish_5000"),
        InlineKeyboardButton(text="10000", callback_data="SumReplenish_10000"),
        InlineKeyboardButton(text="25000", callback_data="SumReplenish_25000"),
    ],
]
BalanceSumKeyboard = InlineKeyboardMarkup(inline_keyboard=BalanceSum)


GetAllHistory = [
    [
        InlineKeyboardButton(
            text="Показать все операции", callback_data="Get_All_History"
        )
    ]
]
GetAllHistoryKeyboard = InlineKeyboardMarkup(inline_keyboard=GetAllHistory)

CheckTransButton = [
    [InlineKeyboardButton(text="Проверить оплату", callback_data="checkTrans")]
]
CheckTrans = InlineKeyboardMarkup(inline_keyboard=CheckTransButton)


NextOrderListButtonAdmin = [
    [
        InlineKeyboardButton(
            text="⬅️Назад", callback_data="BackOrderListAdmin"
        ),
        InlineKeyboardButton(
            text="Дальше➡️", callback_data="NextOrdersListAdmin"
        ),
    ],
    [
        InlineKeyboardButton(text="id", callback_data="SearchForId"),
        InlineKeyboardButton(text="Ссылка", callback_data="SearchForLink"),
    ],
]
NextOrdersListAdmin = InlineKeyboardMarkup(
    inline_keyboard=NextOrderListButtonAdmin
)


BackOrdersButtonAdmin = [
    [
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data="BackOrderListAdmin"
        )
    ],
    [
        InlineKeyboardButton(text="id", callback_data="SearchForId"),
        InlineKeyboardButton(text="Ссылка", callback_data="SearchForLink"),
    ],
]
BackOrdersListAdmin = InlineKeyboardMarkup(
    inline_keyboard=BackOrdersButtonAdmin
)


OnlyNextOrdersButtonAdmin = [
    [
        InlineKeyboardButton(
            text="Дальше ➡️", callback_data="NextOrdersListAdmin"
        )
    ],
    [
        InlineKeyboardButton(text="id", callback_data="SearchForId"),
        InlineKeyboardButton(text="Ссылка", callback_data="SearchForLink"),
    ],
]
OnlyNextOrdersListAdmin = InlineKeyboardMarkup(
    inline_keyboard=OnlyNextOrdersButtonAdmin
)


NextOrderListButton = [
    [
        InlineKeyboardButton(text="⬅️Назад", callback_data="BackOrderList"),
        InlineKeyboardButton(text="Дальше➡️", callback_data="NextOrdersList"),
    ]
]
NextOrdersList = InlineKeyboardMarkup(inline_keyboard=NextOrderListButton)


BackOrdersButton = [
    [InlineKeyboardButton(text="⬅️ Назад", callback_data="BackOrderList")]
]
BackOrdersList = InlineKeyboardMarkup(inline_keyboard=BackOrdersButton)


NextOrdersButton = [
    [InlineKeyboardButton(text="Дальше ➡️", callback_data="NextOrdersList")]
]
OnlyNextOrdersList = InlineKeyboardMarkup(inline_keyboard=NextOrdersButton)


SearchOrdersAdminButton = [
    [
        InlineKeyboardButton(text="id", callback_data="SearchForId"),
        InlineKeyboardButton(text="Ссылка", callback_data="SearchForLink"),
    ],
]
SearchOrdersAdminKeyboard = InlineKeyboardMarkup(
    inline_keyboard=SearchOrdersAdminButton
)


CheckPersonOrMultiButton = [
    [
        InlineKeyboardButton(
            text="Персональный", callback_data="personal_check"
        ),
        InlineKeyboardButton(text="Мульти-чек", callback_data="MultiCheck"),
    ]
]
CheckPersonOrMultiKeyboard = InlineKeyboardMarkup(
    inline_keyboard=CheckPersonOrMultiButton
)


BackCheck = [
    [InlineKeyboardButton(text="Назад", callback_data="BacToPersonalCheck")]
]
BackCheckKeyboard = InlineKeyboardMarkup(inline_keyboard=BackCheck)


Bots = [
    [
        InlineKeyboardButton(text="Создать бота", callback_data="CreateBot"),
        InlineKeyboardButton(text="Удалить бота", callback_data="MyBot"),
    ],
    [
        to_main_menu_button,
    ],
]
BotsKeyboard = InlineKeyboardMarkup(inline_keyboard=Bots)


async def check_maxmin_keyboard(max):
    check_button_max = [
        [
            InlineKeyboardButton(
                text="Мин 0,1 руб", callback_data="auto_check_personal_min"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Макс {max} руб",
                callback_data="auto_check_personal_max",
            )
        ],
    ]
    Keyboard = InlineKeyboardMarkup(inline_keyboard=check_button_max)
    return Keyboard


async def check_multi_maxmin_keyboard(max):
    check_button_max = [
        [
            InlineKeyboardButton(
                text="Мин 0,1 руб", callback_data="auto_check_multi_min"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Макс {max} руб", callback_data="auto_check_multi_max"
            )
        ],
    ]
    Keyboard = InlineKeyboardMarkup(inline_keyboard=check_button_max)
    return Keyboard


async def DeleteBot(IdUser):
    bots = await db.AllBotsForUser(IdUser)
    KeyboardDelete = InlineKeyboardBuilder()
    if not bots:
        return [
            "У вас нету привязанных ботов",
            create_back_keyboard(
                data=MyBotCallbackData(action=MyBotAction.view_bots),
            ),
        ]

    answer = "Выберите бота"
    for bot in bots:
        delete_bot = Bot(token=bot[1])
        name = await delete_bot.get_me()
        name = name.username
        BotsButton = InlineKeyboardButton(
            text=name, callback_data=f"con_delete_bot_{bot[1]}"
        )
        KeyboardDelete.add(BotsButton)

    KeyboardDelete.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data=MyBotCallbackData(
                action=MyBotAction.view_bots
            ).pack(),
        )
    )
    res = [answer, KeyboardDelete.as_markup()]
    return res


async def SubscribeCheck(StartCommand):
    ButtonCheckSubscribe = [
        [
            InlineKeyboardButton(
                text="Проверить подписку",
                callback_data=f"checkSubscribe_{StartCommand}",
            )
        ]
    ]
    KeyboardCheckSubscribe = InlineKeyboardMarkup(
        inline_keyboard=ButtonCheckSubscribe
    )
    return KeyboardCheckSubscribe


async def AddChannel(checkid):
    AddChannelButton = [
        [
            InlineKeyboardButton(
                text="Канал", callback_data=f"Channel_{checkid}"
            ),
            InlineKeyboardButton(
                text="Публичная группа", callback_data=f"PublicGroup_{checkid}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="Приватная группа",
                callback_data=f"PrivateGroup_{checkid}",
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад", callback_data="BacToPersonalCheck"
            )
        ],
    ]
    AddChannelKeyboard = InlineKeyboardMarkup(inline_keyboard=AddChannelButton)
    return AddChannelKeyboard


async def DeleteChannel(CheckId):
    DeleteChannelKeyboard = InlineKeyboardBuilder()
    Check = await db.GetCheckForUser(None, CheckId)
    ChannelId = Check[8]
    ChannelResultId = ChannelId.split(",")
    print(ChannelResultId)
    for ID in ChannelResultId:
        if ID != "":
            Channel = await db.GetChannelTittle(ID)
            ButtonCheck = InlineKeyboardButton(
                text=f"{Channel}", callback_data=f"channel_{ID}"
            )
            DeleteChannelButton = InlineKeyboardButton(
                text="удалить", callback_data=f"deletechannel_{ID}"
            )
            DeleteChannelKeyboard.row(ButtonCheck).add(DeleteChannelButton)
    AddSubscribe = InlineKeyboardButton(
        text="добавить подписку", callback_data=f"Add_Subscribe_{Check[5]}"
    )
    DeleteChannelKeyboard.row(AddSubscribe)
    GoBack = InlineKeyboardButton(
        text="⬅️назад", callback_data="BacToPersonalCheck"
    )
    DeleteChannelKeyboard.row(GoBack)
    return DeleteChannelKeyboard.as_markup()


async def ConfirmCheck(TypeCheck):
    change_sum_data = (
        f'GenerateCheck{"ForPersonal" if TypeCheck == "personal" else "Multi"}'
    )

    UserConfirmCheckButton = [
        [
            InlineKeyboardButton(
                text="Подтверждаю",
                callback_data=f"ConfirmCheck_{TypeCheck}",
            ),
            InlineKeyboardButton(
                text="Отклоняю",
                callback_data="personal_check",
            ),
        ],
        [
            InlineKeyboardButton(
                text="Изменить сумму",
                callback_data=change_sum_data,
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                callback_data="BacToPersonalCheck",
            )
        ],
    ]
    UserConfirmCheckKeyboard = InlineKeyboardMarkup(
        inline_keyboard=UserConfirmCheckButton
    )
    return UserConfirmCheckKeyboard


async def GenerateCheckPersonal(user_id):
    print("personal check")
    GenerateCheckKeyboard = InlineKeyboardBuilder()
    GenerateCheckButton = InlineKeyboardButton(
        text="Создать чек", callback_data="GenerateCheckForPersonal"
    )
    checks = await db.GetCheckForUser(user_id)
    GenerateCheckKeyboard.row(GenerateCheckButton)
    PersonalCheck = 0
    if len(checks) > 0:
        for check in checks:
            if check[7] == "personal":
                PersonalCheck += 1
        HowMuchCheck = InlineKeyboardButton(
            text=f"Мои персональные чеки: {PersonalCheck}",
            callback_data="MyPersonalCheck",
        )
        if PersonalCheck != 0:
            GenerateCheckKeyboard.row(HowMuchCheck)
    return GenerateCheckKeyboard.as_markup()


async def GenerateCheckMulti(user_id):
    GenerateCheckKeyboard = InlineKeyboardBuilder()
    GenerateCheckButton = InlineKeyboardButton(
        text="Создать чек", callback_data="GenerateCheckMulti"
    )
    checks = await db.GetCheckForUser(user_id)
    GenerateCheckKeyboard.row(GenerateCheckButton)
    MultiCheck = 0
    if len(checks) > 0:
        for check in checks:
            if check[7] == "multi":
                MultiCheck += 1
        HowMuchCheck = InlineKeyboardButton(
            text=f"Мои мульти чеки: {MultiCheck}", callback_data="MyMultiCheck"
        )
        if MultiCheck != 0:
            GenerateCheckKeyboard.row(HowMuchCheck)
    return GenerateCheckKeyboard.as_markup()


async def AllUserCheck(user_id, status):
    AllUserCheckKeyboard = InlineKeyboardBuilder()
    checks = await db.GetCheckForUser(user_id)
    if status == "multi":
        for check in checks:
            if check[7] == status:
                button = InlineKeyboardButton(
                    text=str(check[2]), callback_data=f"check_{check[0]}"
                )
                AllUserCheckKeyboard.row(button)
    else:
        for check in checks:
            if check[7] == status:
                button = InlineKeyboardButton(
                    text=str(check[2]), callback_data=f"check_{check[0]}"
                )
                AllUserCheckKeyboard.row(button)
    return AllUserCheckKeyboard.as_markup()


async def ForPersonalUserResultCheck(LinkCheckId):
    Check = await db.GetCheckForUser(None, None, LinkCheckId)
    if Check[7] == "personal":
        ForPersonalUserResultCheckButton = [
            [
                InlineKeyboardButton(
                    text="💵Отправить", switch_inline_query=f"{LinkCheckId}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Удалить", callback_data=f"DeleteCheck_{LinkCheckId}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️Назад", callback_data="BacToPersonalCheck"
                )
            ],
        ]
        ForPersonalUserResultCheckKeyboard = InlineKeyboardMarkup(
            inline_keyboard=ForPersonalUserResultCheckButton
        )
        return ForPersonalUserResultCheckKeyboard
    else:
        ForMultiCheckButton = [
            [
                InlineKeyboardButton(
                    text="💵Отправить", switch_inline_query=f"{LinkCheckId}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Добавить подписку",
                    callback_data=f"Add_Subscribe_{LinkCheckId}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Посмотреть добавленные каналы",
                    callback_data=f"CheckChannel_{LinkCheckId}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Удалить", callback_data=f"DeleteCheck_{LinkCheckId}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️Назад", callback_data="BacToPersonalCheck"
                )
            ],
        ]
        ForMultiCheckKeyboard = InlineKeyboardMarkup(
            inline_keyboard=ForMultiCheckButton
        )
        return ForMultiCheckKeyboard


async def confirm_delete(checkID):
    ConfirmButton = [
        [
            InlineKeyboardButton(
                text="✅Да", callback_data=f"confirm_delete_{checkID}"
            ),
            InlineKeyboardButton(
                text="❌Нет", callback_data="no_confirm_delete"
            ),
        ]
    ]
    confirm_delete_keyboard = InlineKeyboardMarkup(
        inline_keyboard=ConfirmButton
    )
    return confirm_delete_keyboard


async def confirm_bot(BotID):
    ConfirmButton = [
        [
            InlineKeyboardButton(
                text="✅Да",
                callback_data=f"delete_bot_{BotID}",
            ),
            InlineKeyboardButton(
                text="❌Нет",
                callback_data=MyBotCallbackData(
                    action=MyBotAction.view_bots
                ).pack(),
            ),
        ]
    ]
    confirm_delete_keyboard = InlineKeyboardMarkup(
        inline_keyboard=ConfirmButton
    )
    return confirm_delete_keyboard


async def TegroPay(url, crypto_bot_url):
    PayKeyboard = InlineKeyboardBuilder()
    PayButton = InlineKeyboardButton(text="💳Банковской картой", url=url)
    TegroMoney = InlineKeyboardButton(text="💰USDT (Tegro Pay)", url=url)
    CryptoBot = InlineKeyboardButton(text="💎Crypto Bot", url=crypto_bot_url)
    PayKeyboard.row(PayButton).row(TegroMoney).row(CryptoBot)
    return PayKeyboard.as_markup()


async def CategoryMarkup(act):
    CategoryInlineMarkup = InlineKeyboardBuilder()
    # if config.Service == "All":
    #     categories = await db.GetCategory()
    # else:
    #     categories = await db.GetCategory(config.Service)
    categories = db.get_categories_for_services(
        services_names=provider_manager.get_active_services_names()
    )
    for category in categories:
        if category[2] == "None":
            button = InlineKeyboardButton(
                text=category[1], callback_data=f"{act}_category_{category[0]}"
            )
            CategoryInlineMarkup.row(button)
    return CategoryInlineMarkup.as_markup()


async def SubCategory(act, ParentId):
    CategoryInlineMarkup = InlineKeyboardBuilder()
    categories = db.get_categories_for_services(
        services_names=provider_manager.get_active_services_names(),
        parent_id=ParentId,
    )
    for category in categories:
        if category[2] != "None":
            button = InlineKeyboardButton(
                text=category[1],
                callback_data=f"{act}_subcategory_{category[0]}",
            )
            CategoryInlineMarkup.row(button)
    return CategoryInlineMarkup.as_markup()


async def SubCategoryMarkup(act):
    CategoryInlineMarkup = InlineKeyboardBuilder()
    categories = db.get_categories_for_services(
        provider_manager.get_active_services_names()
    )
    for category in categories:
        if category[2] != "None":
            button = InlineKeyboardButton(
                text=category[1], callback_data=f"{act}_category_{category[0]}"
            )
            CategoryInlineMarkup.row(button)
    return CategoryInlineMarkup.as_markup()


async def CategoryAndSubCategory(act):
    CategoryInlineMarkup = InlineKeyboardBuilder()
    categories = await db.GetCategory()
    for category in categories:
        button = InlineKeyboardButton(
            text=category[1], callback_data=f"{act}_category_{category[0]}"
        )
        CategoryInlineMarkup.row(button)
    return CategoryInlineMarkup.as_markup()


async def CheckProduct(act, ParentId):
    ProductInlineMarkup = InlineKeyboardBuilder()
    product = await db.GetProduct(ParentId)
    for products in product:
        button = InlineKeyboardButton(
            text=products[2], callback_data=f"{act}_product_{products[0]}"
        )
        ProductInlineMarkup.row(button)
    return ProductInlineMarkup.as_markup()
