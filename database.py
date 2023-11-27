import logging
import datetime
import sqlite3 as sq
from typing import Any, Dict, List

from core.service_provider.order_status import OrderStatus

logger = logging.getLogger(__name__)

connection = sq.connect("./database.db")


def sql_start():
    if connection:
        logger.info("Database connected successfully")
    else:
        raise Exception("Critical error! Failed to connect to database!")

    cursor = connection.cursor()

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
            service_id INTEGER NOT NULL,
            service_provider TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1
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
            affiliate_id INTEGER,
            bot_id INTEGER
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
            id_channel TEXT,
            total_quantity INTEGER NOT NULL
        )"""
    )
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS Bots(
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            api_key TEXT NOT NULL,
            id_user INTEGER NOT NULL,
            bot_username TEXT
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


def add_category(
    name: str,
    parent_id: int | None = None,
) -> int | None:
    cursor = connection.cursor()
    result = cursor.execute(
        f"SELECT id FROM category WHERE name = '{name}'"
        f"AND parent_id = '{parent_id}'"
    ).fetchone()
    if not result:
        result = cursor.execute(
            f"INSERT INTO category (name, parent_id)"
            f" VALUES ('{name}', '{parent_id}')"
            " RETURNING RowId"
        ).fetchone()
        connection.commit()

    return result[0]


def get_subcategories(
    name,
    category_id,
):
    cursor = connection.cursor()
    name = cursor.execute(
        f"SELECT id FROM category WHERE name = '{name}'"
        f" AND parent_id = '{category_id}'"
    )
    return name.fetchone()[0]


def get_products(
    provider_name: str,
) -> List[Dict[str, Any]]:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    products = cursor.execute(
        f"SELECT * FROM product WHERE service_provider = '{provider_name}'"
    ).fetchall()

    return products


def set_product_is_active(
    product_id: int,
    is_active: bool,
):
    cursor = connection.cursor()
    cursor.execute(
        f"""UPDATE product SET is_active = '{int(is_active)}'
        WHERE id = '{product_id}'"""
    )
    connection.commit()


def update_product(
    service_id: int,
    min_quantity: int,
    max_quantity: int,
    price: int,
):
    cursor = connection.cursor()
    cursor.execute(
        f"""UPDATE product SET
        minorder = '{min_quantity}',
        maxorder = '{max_quantity}',
        price = '{price}'
        WHERE service_id = '{service_id}'"""
    )
    connection.commit()


def add_product(
    category_id: int,
    name: str,
    min_quantity: int,
    max_quantity: int,
    price: float,
    service_id: int,
    service_provider: str,
    is_active: bool = True,
):
    cursor = connection.cursor()
    product = cursor.execute(
        f"""SELECT name FROM product
        WHERE category_id = '{category_id}' AND name = '{name}'"""
    ).fetchone()
    if not product:
        cursor.execute(
            f"""INSERT INTO product (
                    category_id, name, minorder, maxorder, price, service_id,
                    service_provider
                ) VALUES (
                    '{category_id}', '{name}', '{min_quantity}',
                    '{max_quantity}', '{price}', '{service_id}',
                    '{service_provider}'
                )"""
        )
        connection.commit()
        res = "товар успешно добавлен"
        return res
    else:
        res = "такой товар уже есть"
        return res


async def add_user(
    user_id: int,
    bot_id: int,
):
    cursor = connection.cursor()

    cursor.execute(
        f"""INSERT INTO user (user_id, balance, check_activate, bot_id)
        VALUES ('{user_id}', '{0}', '{0}', '{bot_id}')"""
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


async def is_user_exists(user_id: int) -> bool:
    cursor = connection.cursor()
    result = cursor.execute(
        f"""SELECT id FROM user WHERE user_id = '{user_id}'"""
    ).fetchall()
    return bool(len(result))


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


async def GetChannelTitle(ChannelId):
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
    total_quantity=1,
) -> int:
    cursor = connection.cursor()
    cursor.execute(
        f"""INSERT INTO CheckForUser (
            from_user_id, sum, quantity, url, linkcheckid, typecheck,
            total_quantity) VALUES (
                '{user_id}', '{price}', '{quantity}', '{url}', '{linkcheckid}',
                '{TypeCheck}', '{total_quantity}')
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
    IDDeletes.remove(str(ChannelID))
    Id_channel = ",".join(IDDeletes)
    cursor.execute(
        f"""UPDATE CheckForUser SET id_channel = '{Id_channel}'
        WHERE id = '{RealCheckId}'"""
    )
    connection.commit()


def add_bot(
    api_token: str,
    id_user: int,
    bot_username: str,
):
    cursor = connection.cursor()
    Bots = cursor.execute(
        f"SELECT * FROM Bots WHERE api_key = '{api_token}'"
    ).fetchone()
    if not Bots:
        cursor.execute(
            f"""INSERT INTO Bots (api_key, id_user, bot_username) VALUES (
                '{api_token}', '{id_user}', '{bot_username}')"""
        )
        connection.commit()
        return True
    else:
        return False


def delete_bot(api_key):
    cursor = connection.cursor()
    cursor.execute(f"DELETE FROM Bots WHERE api_key = '{api_key}'")
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


def get_bot_data_by_id(bot_id: int) -> Dict[str, Any] | None:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    result = cursor.execute(f"SELECT * FROM Bots WHERE id = '{bot_id}'")

    return result.fetchone()


def update_bot_username(
    bot_id: int,
    username: str,
):
    cursor = connection.cursor()

    cursor.execute(
        f"""UPDATE Bots SET bot_username = '{username}'
        WHERE id = '{bot_id}'""",
    )

    connection.commit()


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


def set_paylink_paid(paylink_id: int, amount: float):
    cursor = connection.cursor()

    cursor.execute(
        f"""UPDATE Paylink SET status = 'paid', amount = '{amount}'
          WHERE id = '{paylink_id}'""",
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


def get_active_categories(
    limit: int,
    page: int,
    services: List[str],
) -> List[Dict[str, Any]]:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    query = f"""SELECT DISTINCT category.* FROM category
            LEFT JOIN category as subcategory
                ON subcategory.parent_id = category.id
            LEFT JOIN product
                ON category.id = product.category_id
                OR subcategory.id = product.category_id
            WHERE category.parent_id = 'None' AND product.is_active = 1
            AND product.service_provider IN ({",".join(["?"] * len(services))})
            LIMIT ? OFFSET ?"""

    params = [*services, limit + 1, (page - 1) * limit]

    result = cursor.execute(query, params)

    return result.fetchall()


def get_active_subcategories(
    limit: int,
    page: int,
    services: List[str],
    parent_id: int | None = None,
) -> List[Dict[str, Any]]:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    query = f"""SELECT DISTINCT category.* FROM category
        INNER JOIN product ON category.id = product.category_id
        WHERE category.parent_id = ? AND product.is_active = 1
        AND product.service_provider IN ({",".join(["?"] * len(services))})
        LIMIT ? OFFSET ?"""

    params = [parent_id, *services, limit + 1, (page - 1) * limit]

    result = cursor.execute(query, params)

    return result.fetchall()


def get_active_products(
    limit: int,
    page: int,
    category_id: int,
    services: List[str],
) -> List[Dict[str, Any]]:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    query = f"""SELECT * FROM product
        WHERE category_id = ? AND is_active = 1
        AND service_provider IN ({",".join(["?"] * len(services))})
        LIMIT ? OFFSET ?"""

    params = [category_id, *services, limit + 1, (page - 1) * limit]

    result = cursor.execute(query, params)

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
        f"""SELECT orders.*, product.name, product.service_provider FROM orders
        LEFT JOIN product ON orders.product_id = product.id
        WHERE orders.id = '{order_id}'"""
    )

    return result.fetchone()


def get_orders_for_pagination(
    user_id: int | None = None,
    order_id_like: int | None = None,
    statuses: List[OrderStatus] | None = None,
    limit: int | None = None,
    page: int | None = None,
    user_id_like: str | None = None,
    link_like: str | None = None,
) -> List[Dict[str, Any]]:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    query = """SELECT orders.*, product.name FROM orders
            LEFT JOIN product ON orders.product_id = product.id"""

    if any((user_id, statuses, user_id_like, link_like)):
        query += " WHERE"

        conditions = []

        if user_id:
            conditions.append(f"user_id = '{user_id}'")

        if user_id_like:
            conditions.append(f"user_id LIKE '%{str(user_id_like)}%'")

        if statuses:
            statuses_string = ",".join(
                [f"'{status.value}'" for status in statuses]
            )
            conditions.append(f"status IN ({statuses_string})")

        if link_like:
            conditions.append(f"url LIKE '%{link_like}%'")

        if order_id_like:
            conditions.append(
                f"order_id LIKE '%{str(order_id_like)}%' OR orders.id = '{str(order_id_like)}'"  # noqa
            )

        query += " " + " AND ".join(conditions)

    if limit:
        query += f" LIMIT {limit + 1}"
    if page:
        query += f" OFFSET {(page - 1) * limit}"

    result = cursor.execute(query)

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
        WHERE service_provider = '{service}'
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


def get_bots() -> List[Dict[str, Any]]:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    result = cursor.execute("""SELECT * FROM Bots""")

    return result.fetchall()


def get_paid_orders(service: str) -> List[Dict[str, Any]]:
    cursor = connection.cursor()
    cursor.row_factory = dict_factory

    result = cursor.execute(
        f"""SELECT orders.* FROM orders
        LEFT JOIN product ON orders.product_id = product.id
        WHERE service_provider = '{service}'
        AND status = '{OrderStatus.NEW.value}'"""
    )

    return result.fetchall()


def update_bot(
    bot_id: int,
    token: str,
):
    cursor = connection.cursor()

    cursor.execute(
        f"""UPDATE Bots SET api_key = '{token}' WHERE id = '{bot_id}'"""
    )

    connection.commit()


def update_user_bot(
    user_id: int,
    bot_id: int,
):
    cursor = connection.cursor()

    cursor.execute(
        f"""UPDATE user SET bot_id = '{bot_id}' WHERE user_id = '{user_id}'"""
    )

    connection.commit()


def get_users_tg_ids_by_bot_id(bot_id: int) -> List[int]:
    cursor = connection.cursor()

    result = cursor.execute(
        f"""SELECT user_id FROM user WHERE bot_id = '{bot_id}'"""
    )

    ids = [user_id[0] for user_id in result.fetchall()]

    return ids
