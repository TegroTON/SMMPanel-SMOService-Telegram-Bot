import logging
import datetime
import sqlite3 as sq
from typing import Any, Dict, List

from core.service_provider.order_status import OrderStatus

logger = logging.getLogger(__name__)

connection = sq.connect("./database.db")


def sql_start():
    cursor = connection.cursor()
    # if connection:
    logger.info("Database connected successfully")
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS category (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            name TEXT NOT NULL,
            parent_id INTEGER,
            service INTEGER
        )"""
    )
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS product (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            minorder INTEGER,
            maxorder INTEGER NOT NULL,
            price INTEGER NOT NULL,
            service_id INTEGER NOT NULL
        )"""
    )
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            sum INTEGER NOT NULL,
            url TEXT NOT NULL,
            date DATETIME,
            order_id INTEGER,
            status TEXT,
            refund INTEGER,
            bot_id INTEGER
        )"""
    )
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS  user(
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            user_id INTEGER NOT NULL,
            balance FLOAT NOT NULL,
            check_activate INTEGER,
            affiliate_id INTEGER
        )"""
    )
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS Channel(
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            channel_id INTEGER NOT NULL,
            channel_name TEXT NOT NULL,
            channel_url TEXT
        )"""
    )
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS CheckForUser(
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            from_user_id INTEGER NOT NULL,
            sum INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            url TEXT NOT NULL,
            linkcheckid INTEGER NOT NULL,
            UserActivate TEXT,
            typecheck TEXT NOT NULL,
            id_channel TEXT
        )"""
    )
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS Bots(
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            api_key TEXT NOT NULL,
            id_user INTEGER NOT NULL
        )"""
    )
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS history(
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            user_id TEXT NOT NULL,
            sum INTEGER NOT NULL,
            type TEXT NOT NULL,
            date DATETIME NOT NULL,
            time DATETIME NOT NULL,
            from_user_id INTEGER,
            order_id INTEGER
        )"""
    )
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS paylink(
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            user_id BIGINTEGER NOT NULL,
            order_id VARCHAR(100) NOT NULL,
            payment_system VARCHAR(100) NOT NULL,
            bot_id INTEGER NOT_NULL,
            amount FLOAT NOT NULL,
            currency VARCHAR(10) NOT NULL,
            created_at DATETIME NOT NULL,
            status VARCHAR(20) NOT NULL
        )"""
    )

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS service(
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            name VARCHAR(50) NOT NULL UNIQUE,
            is_active BOOLEAN NOT NULL DEFAULT 1
        )
        """
    )

    connection.commit()


sql_start()


def dict_factory(cursor, row):
    data = {}
    for idx, col in enumerate(cursor.description):
        data[col[0]] = row[idx]
    return data


async def AddCategory(NameCategory, Service, ParentID=None):
    cursor = connection.cursor()
    Category = cursor.execute(
        f"SELECT name FROM category WHERE name = '{NameCategory}'"
        f"AND parent_id = '{ParentID}'"
    ).fetchone()
    if not Category:
        cursor.execute(
            f"INSERT INTO category (name, parent_id, service)"
            f" VALUES ('{NameCategory}', '{ParentID}', '{Service}')"
        )
        connection.commit()
        res = "Категория успешно добавлена"
        return res
    else:
        res = "Такая категория уже существует"
        return res


async def GetIdParentCategory(NameCategory, Service, IdCategory):
    cursor = connection.cursor()
    NameCategory = cursor.execute(
        f"SELECT id FROM category WHERE name = '{NameCategory}'"
        f" AND service = '{Service}' AND parent_id = '{IdCategory}'"
    )
    return NameCategory.fetchone()[0]


async def GetCategory(service=None):
    cursor = connection.cursor()
    if service is None:
        cursor.execute("""SELECT id, name, parent_id FROM category""")
    else:
        cursor.execute(
            f"""SELECT id, name, parent_id FROM category
            WHERE service = '{service}'"""
        )
    try:
        return cursor.fetchall()
    except Exception as e:
        print(e)
        return None


async def GetSubCategory(IdCategory):
    cursor = connection.cursor()
    Category = cursor.execute(
        f"""SELECT id, name, parent_id FROM category
        WHERE parent_id = '{IdCategory}'"""
    ).fetchall()
    if not Category:
        return None
    else:
        return Category


async def DeleteCategory(id):
    cursor = connection.cursor()
    cursor.execute(
        f"DELETE FROM category WHERE id = '{id}' OR parent_id = '{id}'"
    )
    res = "категории и подкатегории успешно удаленны"
    connection.commit()
    return res


async def GetServiceCategory(id):
    cursor = connection.cursor()
    service = cursor.execute(
        f"""SELECT service FROM category WHERE id = '{id}'"""
    ).fetchone()[0]
    return service


async def AddProduct(
    ParentID, ProductName, MinOrder, MaxOrder, Price, ServiceId
):
    cursor = connection.cursor()
    Category = cursor.execute(
        f"""SELECT name FROM product
        WHERE category_id = '{ParentID}' AND name = '{ProductName}'"""
    ).fetchone()
    if not Category:
        cursor.execute(
            f"""INSERT INTO product (
                    category_id, name, minorder, maxorder, price, service_id
                ) VALUES (
                    '{ParentID}', '{ProductName}', '{MinOrder}', '{MaxOrder}',
                    '{Price}', '{ServiceId}'
                    )"""
        )
        connection.commit()
        res = "товар успешно добавлен"
        return res
    else:
        res = "такой товар уже есть"
        return res


async def GetProduct(ParentId):
    cursor = connection.cursor()
    product = cursor.execute(
        f"""SELECT * FROM product WHERE category_id = '{ParentId}'"""
    )
    if not product:
        return None
    else:
        return product.fetchall()


async def GetProductServiceId(ProductId):
    cursor = connection.cursor()
    ServiceId = cursor.execute(
        f"""SELECT service_id FROM product WHERE id = '{ProductId}'"""
    ).fetchone()
    return ServiceId


async def GetOneProduct(product_id):
    cursor = connection.cursor()
    product = cursor.execute(
        f"""SELECT * FROM product WHERE id = '{product_id}'"""
    ).fetchone()
    if not product:
        return None
    else:
        return product


async def DeleteProduct(ProductId):
    cursor = connection.cursor()
    cursor.execute(f"DELETE FROM product WHERE id = '{ProductId}'")
    res = "Товар успешно удален успешно удаленны"
    connection.commit()
    return res


async def GetBalance(user_id):
    cursor = connection.cursor()
    balance = cursor.execute(
        f"""SELECT balance FROM user WHERE user_id = '{user_id}'"""
    ).fetchone()
    return balance


async def CheckUserInBalance(user_id):
    cursor = connection.cursor()
    checkUser = cursor.execute(
        f"""SELECT balance FROM user WHERE user_id = '{user_id}'"""
    ).fetchone()
    if not checkUser:
        return False
    else:
        return True


async def add_user(user_id: int):
    cursor = connection.cursor()

    cursor.execute(
        f"""INSERT INTO user (user_id, balance, check_activate)
        VALUES ('{user_id}', '{0}', '{0}')"""
    )

    connection.commit()


def update_user_affiliate(
    user_id: int,
    affiliate_id: int,
):
    cursor = connection.cursor()

    cursor.execute(
        f"""UPDATE user SET affiliate_id = '{affiliate_id}'
        WHERE user_id = '{user_id}'"""
    )

    connection.commit()


async def GetUsers():
    cursor = connection.cursor()
    return cursor.execute("""SELECT user_id FROM user""")


async def UpdateBalance(user_id, Sum):
    cursor = connection.cursor()
    cursor.execute(
        f"""UPDATE user SET balance = balance + '{Sum}'
        WHERE user_id = '{user_id}'"""
    )
    connection.commit()


async def WriteOffTheBalance(user_id, Sum):
    cursor = connection.cursor()
    cursor.execute(
        f"""UPDATE user SET balance = balance - '{Sum}'
        WHERE user_id = '{user_id}' """
    )
    connection.commit()


async def AddOrders(
    user_id, product_id, quantity, Sum, ServiceId, url, order_id, status
):
    cursor = connection.cursor()
    date = datetime.datetime.now()
    cursor.execute(
        f"""INSERT INTO orders (
            user_id, product_id, service_id, quantity, sum, url, date,
            order_id, status
            ) VALUES (
                '{user_id}', '{product_id}', '{ServiceId}','{quantity}',
                '{Sum}', '{url}','{date}', '{order_id}', '{status}'
                )"""
    )
    connection.commit()
    res = "Заказ получен"
    return res


async def UpdateOrderStatus(order_id, status):
    cursor = connection.cursor()
    cursor.execute(
        f"""UPDATE orders SET status = '{status}'
        WHERE order_id = '{order_id}'"""
    )
    connection.commit()


async def GetProductName(id):
    cursor = connection.cursor()
    name = cursor.execute(
        f"""SELECT name, category_id FROM product WHERE id = '{id}'"""
    ).fetchone()
    return name


async def GetOrders(user_id=None, Id=None, Link=None):
    cursor = connection.cursor()
    if Id is not None:
        orders = cursor.execute(
            f"""SELECT * FROM orders WHERE order_id = '{Id}'"""
        ).fetchall()
    elif Link is not None:
        orders = cursor.execute(
            f"""SELECT * FROM orders WHERE url = '{Link}'"""
        ).fetchall()
    elif user_id is not None:
        orders = cursor.execute(
            f"""SELECT * FROM orders WHERE user_id = '{user_id}'"""
        ).fetchall()
    elif user_id is None:
        orders = cursor.execute("""SELECT * FROM orders""").fetchall()
    return orders


async def Orders():
    cursor = connection.cursor()
    orders = cursor.execute("""SELECT * FROM orders""").fetchall()
    return orders


async def is_user_exists(user_id: int) -> bool:
    cursor = connection.cursor()
    result = cursor.execute(
        f"""SELECT id FROM user WHERE user_id = '{user_id}'"""
    ).fetchall()
    return bool(len(result))


async def AddUserReferral(user_id, referral_id=None):
    cursor = connection.cursor()
    if referral_id is not None:
        cursor.execute(
            f"""INSERT INTO Referral (user_id, referral_id) VALUES (
                '{user_id}', '{referral_id}')"""
        )
    else:
        cursor.execute(
            f"""INSERT INTO Referral (user_id) VALUES ('{user_id}')"""
        )

    connection.commit()


async def GetUserCheckActivate(user_id):
    cursor = connection.cursor()
    return cursor.execute(
        f"""SELECT check_activate FROM user
        WHERE user_id = '{user_id}'"""
    ).fetchone()[0]


async def UpdateCheckActivate(user_id):
    cursor = connection.cursor()
    cursor.execute(
        f"""UPDATE user SET check_activate = check_activate + 1
        WHERE user_id = '{user_id}'"""
    )
    connection.commit()


async def CountReferrals(user_id):
    cursor = connection.cursor()
    return cursor.execute(
        f"""SELECT COUNT(id) as count FROM Referral
        WHERE referral_id = '{user_id}'"""
    ).fetchone()[0]


async def GetReferral(user_id):
    cursor = connection.cursor()
    return cursor.execute(
        f"""SELECT referral_id FROM Referral WHERE user_id = '{user_id}'"""
    ).fetchone()[0]


async def UpdateMoneyReferral(user_id, sum):
    cursor = connection.cursor()
    cursor.execute(
        f"""UPDATE Referral SET referral_money = '{sum}'
        WHERE user_id = '{user_id}'"""
    )
    connection.commit()


async def GetMoneyReferral(user_id):
    cursor = connection.cursor()
    money = cursor.execute(
        f"""SELECT referral_money FROM Referral WHERE user_id = '{user_id}'"""
    ).fetchone()[0]
    return money


async def AddChanel(channel_id, Name, Url):
    cursor = connection.cursor()
    channel = cursor.execute(
        f"""SELECT * FROM Channel WHERE channel_id = '{channel_id}'"""
    ).fetchone()
    if not channel:
        cursor.execute(
            f"""INSERT INTO Channel (channel_id, channel_name, channel_url)
            VALUES ('{channel_id}', '{Name}', '{Url}')"""
        )
    connection.commit()


async def GetChannelTittle(ChannelId):
    cursor = connection.cursor()
    channel = cursor.execute(
        f"""SELECT channel_name FROM Channel
        WHERE channel_id = '{ChannelId}'"""
    ).fetchone()[0]
    return channel


async def GetChannelId(ChannelUrl):
    cursor = connection.cursor()
    channel = cursor.execute(
        f"""SELECT channel_id FROM Channel
        WHERE channel_name = '{ChannelUrl}'"""
    ).fetchone()
    return channel


async def GetChannelUrl(ChannelID):
    cursor = connection.cursor()
    result = cursor.execute(
        f"""SELECT channel_url FROM Channel WHERE channel_id = '{ChannelID}'"""
    ).fetchone()
    return result[0] if result else None


async def AddCheck(
    user_id,
    price,
    url,
    linkcheckid,
    TypeCheck,
    quantity=1,
) -> int:
    cursor = connection.cursor()
    cursor.execute(
        f"""INSERT INTO CheckForUser (
            from_user_id, sum, quantity, url, linkcheckid, typecheck)
            VALUES (
                '{user_id}', '{price}', '{quantity}', '{url}', '{linkcheckid}',
                '{TypeCheck}')
            RETURNING RowId
            """
    )
    check_id = cursor.fetchone()[0]
    connection.commit()
    return check_id


async def GetCheckForUser(user_id=None, CheckId=None, LinkCheckId=None):
    cursor = connection.cursor()
    if user_id is not None:
        check = cursor.execute(
            f"""SELECT * FROM CheckForUser WHERE from_user_id = '{user_id}'"""
        ).fetchall()
    elif CheckId is not None:
        check = cursor.execute(
            f"""SELECT * FROM CheckForUser WHERE id = '{CheckId}'"""
        ).fetchone()
    elif LinkCheckId is not None:
        check = cursor.execute(
            f"""SELECT * FROM CheckForUser
            WHERE linkcheckid = '{LinkCheckId}'"""
        ).fetchone()
    return check


async def DeleteCheck(CheckId=None, Url=None, LinkCheckId=None):
    cursor = connection.cursor()
    if CheckId is not None:
        cursor.execute(f"DELETE FROM CheckForUser WHERE id = '{CheckId}'")
        connection.commit()
    elif Url is not None:
        cursor.execute(f"DELETE FROM CheckForUser WHERE url = '{Url}'")
        connection.commit()
    elif LinkCheckId is not None:
        cursor.execute(
            f"DELETE FROM CheckForUser WHERE linkcheckid = '{LinkCheckId}'"
        )
        connection.commit()


async def UpdateQuantityAndActivate(LinkIdCheck, IdActivate):
    cursor = connection.cursor()
    cursor.execute(
        f"""UPDATE CheckForUser SET quantity = quantity - 1
        WHERE linkcheckid = '{LinkIdCheck}'"""
    )
    UserActivate = cursor.execute(
        f"""SELECT USerActivate FROM CheckForUser
        WHERE linkcheckid = '{LinkIdCheck}'"""
    ).fetchone()[0]
    if UserActivate is None or UserActivate == "":
        Id_User = f"{IdActivate}"
    else:
        Id_User = f"{UserActivate},{IdActivate}"
    cursor.execute(
        f"""UPDATE CheckForUser SET UserActivate = '{Id_User}'
        WHERE linkcheckid = '{LinkIdCheck}'"""
    )
    connection.commit()


async def UpdateChannel(LinkIdCheck, Id_Channel):
    cursor = connection.cursor()
    ChanID = cursor.execute(
        f"""SELECT id_channel FROM CheckForUser
        WHERE linkcheckid = '{LinkIdCheck}'"""
    ).fetchone()[0]
    if ChanID is None or ChanID == "":
        Id_Channel = f"{Id_Channel}"
    else:
        Id_Channel = f"{ChanID},{Id_Channel}"
    cursor.execute(
        f"""UPDATE CheckForUser SET id_channel = '{Id_Channel}'
        WHERE linkcheckid = '{LinkIdCheck}'"""
    )
    connection.commit()


async def DeleteChannelFromCheck(RealCheckId, ChannelID):
    cursor = connection.cursor()
    ChanID = cursor.execute(
        f"""SELECT id_channel FROM CheckForUser WHERE id = '{RealCheckId}'"""
    ).fetchone()[0]
    IDDeletes = ChanID.split(",")
    print(ChannelID)
    print(IDDeletes)
    IDDeletes.remove(str(ChannelID))
    Id_channel = ",".join(IDDeletes)
    # Id_channel = ""
    # for IDdelete in IDDeletes:
    #     if IDdelete != "" and int(IDdelete) != int(ChannelID):
    #         Id_channel = f"{Id_channel},{IDdelete}"
    cursor.execute(
        f"""UPDATE CheckForUser SET id_channel = '{Id_channel}'
        WHERE id = '{RealCheckId}'"""
    )
    connection.commit()


async def AddBots(api_token, id_user):
    cursor = connection.cursor()
    Bots = cursor.execute(
        f"SELECT * FROM Bots WHERE api_key = '{api_token}'"
    ).fetchone()
    if not Bots:
        cursor.execute(
            f"""INSERT INTO Bots (api_key, id_user) VALUES (
                '{api_token}', '{id_user}')"""
        )
        connection.commit()
        return True
    else:
        return False


async def AllBotsForUser(id_user):
    cursor = connection.cursor()
    Bots = cursor.execute(
        f"SELECT * FROM Bots WHERE id_user = '{id_user}'"
    ).fetchall()
    return Bots


async def DeleteBot(api_key):
    cursor = connection.cursor()
    cursor.execute(f"DELETE FROM Bots WHERE api_key = '{api_key}'")
    connection.commit()


async def Refund(id):
    cursor = connection.cursor()
    cursor.execute(f"""UPDATE orders SET refund = 1 WHERE id = '{id}' """)
    connection.commit()


async def GetRefundStatus(id):
    cursor = connection.cursor()
    Status = cursor.execute(
        f"""SELECT refund FROM orders WHERE id = '{id}'"""
    ).fetchone()[0]
    return Status


async def WriteOffTheReferral(referral_id, sum_referral):
    cursor = connection.cursor()
    cursor.execute(
        f"""UPDATE Referral SET
        referral_money = referral_money - '{sum_referral}'
        WHERE user_id = '{referral_id}'"""
    )
    connection.commit()


async def Add_History(
    user_id,
    sum,
    type,
    from_user_id: int | None = None,
    order_id: int | None = None,
):
    cursor = connection.cursor()
    date = datetime.date.today()
    time = datetime.datetime.now().time()
    cursor.execute(
        f"""INSERT INTO history (user_id, sum, type, date, time, from_user_id,
            order_id) VALUES (
            '{user_id}', '{sum}', '{type}', '{date}', '{time}',
            '{from_user_id}', '{order_id}')"""
    )
    connection.commit()


async def Get_History(user_id):
    cursor = connection.cursor()
    res = cursor.execute(
        f"""SELECT * FROM history WHERE user_id = '{user_id}'"""
    ).fetchall()
    return res


# --- --- --- --- --- --- --- --- ---


def get_personal_checks_count(user_id: int) -> int:
    return _get_checks_count_for_user(user_id, "personal")


def get_multi_checks_count(user_id: int) -> int:
    return _get_checks_count_for_user(user_id, "multi")


def _get_checks_count_for_user(user_id: int, check_type: str) -> int:
    cursor = connection.cursor()
    result = cursor.execute(
        "SELECT COUNT(*) FROM CheckForUser"
        f" WHERE from_user_id = '{user_id}' AND typecheck = '{check_type}'"
    )
    try:
        return int(result.fetchone()[0])
    except ValueError:
        return 0


def get_user_balance(user_id: int) -> float:
    cursor = connection.cursor()
    result = cursor.execute(
        "SELECT balance FROM user" f" WHERE user_id = '{user_id}'"
    )
    try:
        return round(float(result.fetchone()[0]), 2)
    except ValueError:
        return 0


def get_checks_for_user(user_id: int, check_type: str) -> List[Any]:
    cursor = connection.cursor()
    result = cursor.execute(
        "SELECT * FROM CheckForUser"
        f" WHERE from_user_id = '{user_id}' AND typecheck = '{check_type}'"
    )
    return result.fetchall()


def get_multi_hecks_for_user(user_id: int) -> List[Any]:
    return get_checks_for_user(user_id, "multi")


def get_personal_checks_for_user(user_id: int) -> List[Any]:
    return get_checks_for_user(user_id, "personal")


def get_check_by_id(check_id: int) -> List[Any]:
    cursor = connection.cursor()
    result = cursor.execute(
        "SELECT * FROM CheckForUser" f" WHERE id = '{check_id}'"
    )
    return result.fetchone()


def get_check_by_check_number(check_number: int) -> Dict[str, Any]:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    result = cursor.execute(
        "SELECT * FROM CheckForUser" f" WHERE linkcheckid = '{check_number}'"
    )

    return result.fetchone()


def get_check_by_user_id_and_check_id(
    user_id: int, check_id: int
) -> List[Any]:
    cursor = connection.cursor()
    result = cursor.execute(
        "SELECT * FROM CheckForUser"
        f" WHERE from_user_id = '{user_id}' AND id = '{check_id}'"
    )
    return result.fetchone()


def delete_check_by_id(check_id: int):
    cursor = connection.cursor()
    cursor.execute(f"DELETE FROM CheckForUser WHERE id = '{check_id}'")
    connection.commit()


def get_all_channels() -> List[Any]:
    cursor = connection.cursor()
    result = cursor.execute("SELECT * FROM Channel")
    return result.fetchall()


def get_channels_for_check(check_id: int) -> List[Any]:
    check = get_check_by_id(check_id)

    if not check or not check[8]:
        return []

    channels_in_check_ids = list(
        filter(lambda channel_id: channel_id != "", check[8].split(","))
    )

    if not channels_in_check_ids:
        return []

    channels = list(
        filter(
            lambda channel: str(channel[1]) in channels_in_check_ids,
            get_all_channels(),
        )
    )

    return channels


def get_channel_by_id(channel_id: int) -> List[Any]:
    cursor = connection.cursor()
    result = cursor.execute(
        "SELECT * FROM Channel" f" WHERE channel_id = '{channel_id}'"
    )
    return result.fetchone()


def get_paylink_data_by_order_id(order_id: str) -> Dict[str, Any]:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory
    result = cursor.execute(
        f"SELECT * FROM Paylink WHERE order_id = '{order_id}'"
    )

    return result.fetchone()


def get_bot_token_by_id(bot_id: int) -> str | None:
    cursor = connection.cursor()
    result = cursor.execute(f"SELECT api_key FROM Bots  WHERE id = '{bot_id}'")
    bot_id = result.fetchone()
    return bot_id[0] if bot_id else None


def get_bot_id_by_token(token: str) -> int | None:
    cursor = connection.cursor()

    result = cursor.execute(f"SELECT id FROM Bots  WHERE api_key = '{token}'")

    bot_id = result.fetchone()
    return bot_id[0] if bot_id else None


def get_bot_data_by_token(token: str) -> Dict[str, Any] | None:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    result = cursor.execute(f"SELECT * FROM Bots WHERE api_key = '{token}'")

    return result.fetchone()


def add_paylink(
    user_id: int,
    order_id: str,
    payment_system: str,
    bot_id: int,
    amount: float,
    currency: str = "RUB",
):
    cursor = connection.cursor()
    result = cursor.execute(
        f"""
        INSERT INTO Paylink
        (user_id, order_id, payment_system, bot_id, amount, created_at, status,
        currency)
        VALUES
        ('{user_id}', '{order_id}', '{payment_system}', '{bot_id}', '{amount}',
            '{datetime.datetime.now()}', 'pending', '{currency}')
        RETURNING RowId
        """
    )
    paylink_id = result.fetchone()[0]
    connection.commit()

    return paylink_id


def update_paylink_order_id(
    paylink_id: int,
    order_id: str,
):
    cursor = connection.cursor()

    cursor.execute(
        f"""UPDATE Paylink SET order_id = '{order_id}'
        WHERE id = '{paylink_id}'""",
    )

    connection.commit()


def set_paylink_paid(paylink_id: int):
    cursor = connection.cursor()

    cursor.execute(
        f"UPDATE Paylink SET status = 'paid' WHERE id = '{paylink_id}'",
    )

    connection.commit()


def update_user_balance(
    user_id: int,
    amount: float,
):
    cursor = connection.cursor()

    cursor.execute(
        f"""UPDATE user SET balance = balance + '{amount}'
        WHERE user_id = '{user_id}'""",
    )

    connection.commit()


def get_affiliate_id(user_id: int) -> int | None:
    cursor = connection.cursor()

    cursor.execute(
        f"""SELECT affiliate_id FROM user WHERE user_id = '{user_id}'"""
    )

    return cursor.fetchone()[0]


def get_referrals(
    user_id: int,
    depth: int = 1,
) -> List[Any]:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    referrals = cursor.execute(
        f"""SELECT * FROM user WHERE affiliate_id = '{user_id}'"""
    ).fetchall()

    while depth > 1:
        for referral in referrals:
            referrals.extend(
                cursor.execute(
                    f"""SELECT * FROM user
                    WHERE affiliate_id = '{referral["user_id"]}'"""
                ).fetchall()
            )

    return referrals


def get_total_bonus_amount(
    user_id: int,
) -> int:
    cursor = connection.cursor()

    cursor.execute(
        f"""SELECT SUM(sum) FROM history
        WHERE user_id = {user_id}
        AND type = 'Бонус - Новый реферал'
        OR type = 'Бонус - Заказ услуги рефералом'"""
    )

    return cursor.fetchone()[0] or 0


def get_categories_for_pagination(
    limit: int,
    page: int,
    services: List[str],
) -> List[Dict[str, Any]]:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    query = f"""SELECT * FROM category WHERE parent_id = ?
            AND service IN ({','.join(['?'] * len(services))})
            LIMIT ? OFFSET ?"""

    params = ["None", *services, limit + 1, (page - 1) * limit]

    result = cursor.execute(query, params)

    return result.fetchall()


def get_subcategories_for_pagination(
    limit: int,
    page: int,
    services: List[str],
    parent_id: int | None = None,
) -> List[Dict[str, Any]]:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    query = f"""SELECT * FROM category WHERE parent_id = ?
            AND service IN ({','.join(['?'] * len(services))})
            LIMIT ? OFFSET ?"""

    params = [parent_id, *services, limit + 1, (page - 1) * limit]

    result = cursor.execute(query, params)

    return result.fetchall()


def get_products_for_pagination(
    limit: int,
    page: int,
    category_id: int,
) -> List[Dict[str, Any]]:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    query = "SELECT * FROM product WHERE category_id = ? LIMIT ? OFFSET ?"

    result = cursor.execute(
        query, (category_id, limit + 1, (page - 1) * limit)
    )

    return result.fetchall()


def get_product_by_id(
    product_id: int,
) -> Dict[str, Any]:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    result = cursor.execute(f"SELECT * FROM product WHERE id = '{product_id}'")

    return result.fetchone()


def add_order(
    user_id: int,
    product_id: int,
    service_id: int,
    quantity: int,
    total_amount: float,
    url: str,
    bot_id: int | None,
) -> int | None:
    cursor = connection.cursor()

    result = cursor.execute(
        f"""INSERT INTO orders (
            user_id, product_id, service_id, quantity, sum, url, date,
            status, bot_id
        ) VALUES (
            '{user_id}', '{product_id}', '{service_id}', '{quantity}',
            '{total_amount}', '{url}', '{datetime.datetime.now()}',
            '{OrderStatus.PENDING_PAYMENT.value}', '{bot_id}'
        ) RETURNING RowId"""
    )

    internal_order_id = result.fetchone()[0]
    connection.commit()

    return internal_order_id


def get_order_by_id(order_id: int) -> Dict[str, Any]:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    result = cursor.execute(
        f"""SELECT orders.*, product.name, category.service FROM orders
        LEFT JOIN product ON orders.product_id = product.id
        LEFT JOIN category ON product.category_id = category.id
        WHERE orders.id = '{order_id}'"""
    )

    return result.fetchone()


def get_orders_for_pagination(
    user_id: int,
    limit: int,
    page: int,
) -> List[Dict[str, Any]]:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    query = """SELECT orders.*, product.name FROM orders
            LEFT JOIN product ON orders.product_id = product.id
            WHERE user_id = ? LIMIT ? OFFSET ?"""

    result = cursor.execute(query, (user_id, limit + 1, (page - 1) * limit))

    return result.fetchall()


def update_order_status(
    order_id: int,
    status: OrderStatus,
) -> None:
    cursor = connection.cursor()

    cursor.execute(
        f"""UPDATE orders SET status = '{status.value}'
        WHERE id = '{order_id}'"""
    )

    connection.commit()


def update_order_status_and_external_id(
    order_id: int,
    status: OrderStatus,
    external_id: int,
):
    cursor = connection.cursor()

    cursor.execute(
        f"""UPDATE orders SET
        status = '{status.value}', order_id = '{external_id}'
        WHERE id = '{order_id}'"""
    )

    connection.commit()


def get_orders_ids_for_check(service: str) -> List[int]:
    cursor = connection.cursor()

    cursor.execute(
        f"""SELECT orders.id, orders.order_id FROM orders
        LEFT JOIN product ON orders.product_id = product.id
        LEFT JOIN category ON product.category_id = category.id
        WHERE service = '{service}'
        AND status in ('{OrderStatus.STARTING.value}',
        '{OrderStatus.IN_PROGRESS.value}')"""
    )

    return cursor.fetchall()


def get_category_name(
    category_id: int,
) -> str:
    cursor = connection.cursor()

    cursor.execute(
        f"""SELECT name FROM category
        WHERE id = '{category_id}'"""
    )

    return cursor.fetchone()[0]


def get_category_and_subcategory_names(
    subcategory_id: int,
) -> (str, str):
    cursor = connection.cursor()

    cursor.execute(
        f"""SELECT category.name, subcategory.name FROM category
        LEFT JOIN category as subcategory
        ON subcategory.parent_id = category.id
        WHERE subcategory.id = '{subcategory_id}'"""
    )

    return cursor.fetchone()


def get_active_services() -> List[str]:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    result = cursor.execute("""SELECT name FROM service WHERE is_active = 1""")

    return result.fetchall()


def get_services() -> List[Dict[str, Any]]:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    result = cursor.execute("""SELECT * FROM service""")

    return result.fetchall()


def add_service(name: str):
    cursor = connection.cursor()

    cursor.execute(f"""INSERT INTO service (name) VALUES ('{name}')""")

    connection.commit()


def update_service_status(
    name: str,
    status: int,
):
    cursor = connection.cursor()

    cursor.execute(
        f"""UPDATE service SET is_active = '{status}' WHERE name = '{name}'"""
    )

    connection.commit()


def get_categories_for_services(
    services_names: List[str],
    parent_id: int | None = None,
) -> List[str]:
    cursor = connection.cursor()

    query = f"""SELECT * FROM category WHERE parent_id = ?
            AND service IN ({','.join(['?'] * len(services_names))})"""

    params = ["None" if not parent_id else parent_id, *services_names]

    result = cursor.execute(query, params)

    return result.fetchall()


def get_bots_for_user(user_id: int) -> List[Dict[str, Any]]:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    result = cursor.execute(
        f"""SELECT * FROM Bots WHERE id_user = '{user_id}'"""
    )

    return result.fetchall()


def get_paid_orders(service: str) -> List[Dict[str, Any]]:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    result = cursor.execute(
        f"""SELECT orders.* FROM orders
        LEFT JOIN product ON orders.product_id = product.id
        LEFT JOIN category ON product.category_id = category.id
        WHERE category.service = '{service}'
        AND status = '{OrderStatus.NEW.value}'"""
    )

    return result.fetchall()
