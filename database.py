import datetime
import sqlite3 as sq

con = sq.connect('database.db')


def sql_start():
    cursor = con.cursor()
    if con:
        print('Connect')
    cursor.execute('''CREATE TABLE IF NOT EXISTS category (
                 id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
                 name TEXT NOT NULL,
                 parent_id INTEGER,
                 service INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS product (
                     id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
                     category_id INTEGER NOT NULL,
                     name TEXT NOT NULL,
                     minorder INTEGER,
                     maxorder INTEGER NOT NULL,
                     price INTEGER NOT NULL,
                     service_id INTEGER NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
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
                     refund INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS  UserBalance(
                     id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
                     user_id INTEGER NOT NULL,
                     balance FLOAT NOT NULL,
                     check_activate INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS  Referral(
                     id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
                     user_id INTEGER NOT NULL,
                     referral_id INTEGER,
                     referral_money INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Channel(
                     id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
                     channel_id INTEGER NOT NULL,
                     channel_name TEXT NOT NULL,
                     channel_url TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS CheckForUser(
                     id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
                     from_user_id INTEGER NOT NULL,
                     sum INTEGER NOT NULL,
                     quantity INTEGER NOT NULL,
                     url TEXT NOT NULL,
                     linkcheckid INTEGER NOT NULL,
                     UserActivate TEXT,
                     typecheck TEXT NOT NULL,
                     id_channel TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Bots(
                     id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
                     api_key TEXT NOT NULL,
                     id_user INTEGER NOT NULL)''')
    con.commit()


async def AddCategory(NameCategory, Service, ParentID=None):
    cursor = con.cursor()
    Category = cursor.execute(
        f"SELECT name FROM category WHERE name = '{NameCategory}' AND parent_id = '{ParentID}'").fetchone()
    if not Category:
        cursor.execute(f"INSERT INTO category (name, parent_id, service) VALUES ('{NameCategory}', '{ParentID}', '{Service}')")
        con.commit()
        res = 'Категория успешно добавлена'
        return res
    else:
        res = 'Такая категория уже существует'
        return res


async def GetIdParentCategory(NameCategory, Service, IdCategory):
    cursor = con.cursor()
    NameCategory = cursor.execute(f"SELECT id FROM category WHERE name = '{NameCategory}' AND service = '{Service}' AND parent_id = '{IdCategory}' ")
    return NameCategory.fetchone()[0]


async def GetCategory(service=None):
    cursor = con.cursor()
    if service is None:
        cursor.execute(f"""SELECT id, name, parent_id FROM category""")
    else:
        cursor.execute(f"""SELECT id, name, parent_id FROM category WHERE service = '{service}' """)
    try:
        return cursor.fetchall()
    except Exception as e:
        print(e)
        return None


async def GetSubCategory(IdCategory):
    cursor = con.cursor()
    Category = cursor.execute(f"""SELECT id, name, parent_id FROM category WHERE parent_id = '{IdCategory}' """).fetchall()
    if not Category:
        return None
    else:
        return Category


async def DeleteCategory(id):
    cursor = con.cursor()
    cursor.execute(f"DELETE FROM category WHERE id = '{id}' OR parent_id = '{id}' ")
    res = 'категории и подкатегории успешно удаленны'
    con.commit()
    return res


async def GetServiceCategory(id):
    cursor = con.cursor()
    service = cursor.execute(f'''SELECT service FROM category WHERE id = '{id}' ''').fetchone()[0]
    return service


async def AddProduct(ParentID, ProductName, MinOrder, MaxOrder, Price, ServiceId):
    cursor = con.cursor()
    Category = cursor.execute(
        f"SELECT name FROM product WHERE category_id = '{ParentID}' AND name = '{ProductName}'").fetchone()
    if not Category:
        cursor.execute(
            f"INSERT INTO product (category_id, name, minorder, maxorder, price, service_id) VALUES ('{ParentID}', '{ProductName}', '{MinOrder}', '{MaxOrder}', '{Price}', '{ServiceId}')  ")
        con.commit()
        res = 'товар успешно добавлен'
        return res
    else:
        res = 'такой товар уже есть'
        return res


async def GetProduct(ParentId):
    cursor = con.cursor()
    product = cursor.execute(f"""SELECT * FROM product WHERE category_id = '{ParentId}' """)
    if not product:
        return None
    else:
        return product.fetchall()


async def GetProductServiceId(ProductId):
    cursor = con.cursor()
    ServiceId = cursor.execute(f'''SELECT service_id FROM product WHERE id = '{ProductId}' ''').fetchone()
    return ServiceId


async def GetOneProduct(product_id):
    cursor = con.cursor()
    product = cursor.execute(f"""SELECT * FROM product WHERE id = '{product_id}' """).fetchone()
    if not product:
        return None
    else:
        return product


async def DeleteProduct(ProductId):
    cursor = con.cursor()
    cursor.execute(f"DELETE FROM product WHERE id = '{ProductId}'")
    res = 'Товар успешно удален успешно удаленны'
    con.commit()
    return res


async def GetBalance(user_id):
    cursor = con.cursor()
    balance = cursor.execute(f'''SELECT balance FROM UserBalance WHERE user_id = '{user_id}' ''').fetchone()
    return balance


async def CheckUserInBalance(user_id):
    cursor = con.cursor()
    checkUser = cursor.execute(f'''SELECT balance FROM UserBalance WHERE user_id = '{user_id}' ''').fetchone()
    if not checkUser:
        return False
    else:
        return True


async def UserBalance(user_id):
    cursor = con.cursor()
    cursor.execute(
        f'''INSERT INTO UserBalance (user_id, balance, check_activate) VALUES ('{user_id}', '{0}', '{0}') ''')
    con.commit()


async def GetUsers():
    cursor = con.cursor()
    return cursor.execute('''SELECT user_id FROM UserBalance''')


async def UpdateBalance(user_id, Sum):
    cursor = con.cursor()
    cursor.execute(f'''UPDATE UserBalance SET balance = balance + '{Sum}' WHERE user_id = '{user_id}' ''')
    con.commit()


async def WriteOffTheBalance(user_id, Sum):
    cursor = con.cursor()
    cursor.execute(f'''UPDATE UserBalance SET balance = balance - '{Sum}' WHERE user_id = '{user_id}' ''')
    con.commit()


async def AddOrders(user_id, product_id, quantity, Sum, ServiceId, url, order_id, status):
    cursor = con.cursor()
    date = datetime.datetime.now()
    cursor.execute(
        f'''INSERT INTO orders (user_id, product_id, service_id, quantity, sum, url, date, order_id, status) VALUES ('{user_id}', '{product_id}', '{ServiceId}','{quantity}', '{Sum}', '{url}','{date}', '{order_id}', '{status}')''')
    con.commit()
    res = "Заказ получен"
    return res


async def UpdateOrderStatus(order_id, status):
    cursor = con.cursor()
    cursor.execute(f'''UPDATE orders SET status = '{status}' WHERE order_id = '{order_id}' ''')
    con.commit()


async def GetProductName(id):
    cursor = con.cursor()
    name = cursor.execute(f'''SELECT name, category_id FROM product WHERE id = '{id}' ''').fetchone()
    return name


async def GetOrders(user_id=None, Link=None):
    cursor = con.cursor()
    if user_id is None:
        orders = cursor.execute('''SELECT * FROM orders''').fetchall()
    elif Link is not None:
        pass
    else:
        orders = cursor.execute(f'''SELECT * FROM orders WHERE user_id = '{user_id}' ''').fetchall()
    return orders


async def Orders():
    cursor = con.cursor()
    orders = cursor.execute('''SELECT * FROM orders''').fetchall()
    return orders


async def UserExists(user_id):
    cursor = con.cursor()
    res = cursor.execute(f'''SELECT * FROM Referral WHERE user_id = '{user_id}' ''').fetchall()
    return bool(len(res))


async def AddUserReferral(user_id, referral_id=None):
    cursor = con.cursor()
    if referral_id is not None:
        cursor.execute(f'''INSERT INTO Referral (user_id, referral_id) VALUES ('{user_id}', '{referral_id}') ''')
    else:
        cursor.execute(f'''INSERT INTO Referral (user_id) VALUES ('{user_id}') ''')

    con.commit()


async def GetUserCheckActivate(user_id):
    cursor = con.cursor()
    return cursor.execute(f'''SELECT check_activate FROM UserBalance WHERE user_id = '{user_id}' ''').fetchone()[0]


async def UpdateCheckActivate(user_id):
    cursor = con.cursor()
    cursor.execute(f'''UPDATE UserBalance SET check_activate = check_activate + 1 WHERE user_id = '{user_id}' ''')
    con.commit()


async def CountReferrals(user_id):
    cursor = con.cursor()
    return cursor.execute(f'''SELECT COUNT(id) as count FROM Referral WHERE referral_id = '{user_id}' ''').fetchone()[0]


async def GetReferral(user_id):
    cursor = con.cursor()
    return cursor.execute(f'''SELECT referral_id FROM Referral WHERE user_id = '{user_id}' ''').fetchone()[0]


async def UpdateMoneyReferral(user_id, sum):
    cursor = con.cursor()
    cursor.execute(f'''UPDATE Referral SET referral_money = '{sum}' WHERE user_id = '{user_id}' ''')
    con.commit()


async def GetMoneyReferral(user_id):
    cursor = con.cursor()
    money = cursor.execute(f'''SELECT referral_money FROM Referral WHERE user_id = '{user_id}' ''').fetchone()[0]
    return money


async def AddChanel(channel_id, Name, Url):
    cursor = con.cursor()
    channel = cursor.execute(f'''SELECT * FROM Channel WHERE channel_id = '{channel_id}' ''').fetchone()
    if not channel:
        cursor.execute(
            f'''INSERT INTO Channel (channel_id, channel_name, channel_url) VALUES ('{channel_id}', '{Name}', '{Url}') ''')
    con.commit()


async def GetChannelTittle(ChannelId):
    cursor = con.cursor()
    channel = cursor.execute(f'''SELECT channel_name FROM Channel WHERE channel_id = '{ChannelId}' ''').fetchone()[0]
    return channel


async def GetChannelId(ChannelUrl):
    cursor = con.cursor()
    channel = cursor.execute(f'''SELECT channel_id FROM Channel WHERE channel_name = '{ChannelUrl}' ''').fetchone()
    return channel


async def GetChannelUrl(ChannelID):
    cursor = con.cursor()
    channel = cursor.execute(f'''SELECT channel_url FROM Channel WHERE channel_id = '{ChannelID}' ''').fetchone()[0]
    return channel


async def AddCheck(user_id, price, url, linkcheckid, TypeCheck, quantity=1):
    cursor = con.cursor()
    cursor.execute(
        f'''INSERT INTO CheckForUser (from_user_id, sum, quantity, url, linkcheckid, typecheck) VALUES ('{user_id}', '{price}', '{quantity}', '{url}', '{linkcheckid}', '{TypeCheck}') ''')
    con.commit()


async def GetCheckForUser(user_id=None, CheckId=None, LinkCheckId=None):
    cursor = con.cursor()
    if user_id is not None:
        check = cursor.execute(f'''SELECT * FROM CheckForUser WHERE from_user_id = '{user_id}' ''').fetchall()
    elif CheckId is not None:
        check = cursor.execute(f'''SELECT * FROM CheckForUser WHERE id = '{CheckId}' ''').fetchone()
    elif LinkCheckId is not None:
        check = cursor.execute(f'''SELECT * FROM CheckForUser WHERE linkcheckid = '{LinkCheckId}' ''').fetchone()
    return check


async def DeleteCheck(CheckId=None, Url=None, LinkCheckId=None):
    cursor = con.cursor()
    if CheckId is not None:
        cursor.execute(f"DELETE FROM CheckForUser WHERE id = '{CheckId}'")
        con.commit()
    elif Url is not None:
        cursor.execute(f"DELETE FROM CheckForUser WHERE url = '{Url}'")
        con.commit()
    elif LinkCheckId is not None:
        cursor.execute(f"DELETE FROM CheckForUser WHERE linkcheckid = '{LinkCheckId}'")
        con.commit()


async def UpdateQuantityAndActivate(LinkIdCheck, IdActivate):
    cursor = con.cursor()
    cursor.execute(f'''UPDATE CheckForUser SET quantity = quantity - 1 WHERE linkcheckid = '{LinkIdCheck}' ''')
    cursor.execute(f'''UPDATE CheckForUser SET UserActivate = '{IdActivate}, ' WHERE linkcheckid = '{LinkIdCheck}' ''')
    con.commit()


async def UpdateChannel(LinkIdCheck, Id_Channel):
    cursor = con.cursor()
    ChanID = cursor.execute(f'''SELECT id_channel FROM CheckForUser WHERE linkcheckid = '{LinkIdCheck}' ''').fetchone()[0]
    print(ChanID)
    if ChanID is None or ChanID == '':
        Id_Channel = f'{Id_Channel}'
    else:
        Id_Channel = f'{ChanID},{Id_Channel}'
    cursor.execute(f'''UPDATE CheckForUser SET id_channel = '{Id_Channel}' WHERE linkcheckid = '{LinkIdCheck}' ''')
    con.commit()


async def DeleteChannelFromCheck(RealCheckId, ChannelID):
    cursor = con.cursor()
    ChanID = cursor.execute(f'''SELECT id_channel FROM CheckForUser WHERE id = '{RealCheckId}' ''').fetchone()[0]
    IDDeletes = ChanID.split(',')
    Id_channel = ''
    for IDdelete in IDDeletes:
        if IDdelete != '':
            if int(IDdelete) != int(ChannelID):
                Id_channel = f'{Id_channel}, {IDdelete}'
    cursor.execute(f'''UPDATE CheckForUser SET id_channel = '{Id_channel}' WHERE id = '{RealCheckId}' ''')
    con.commit()


async def AddBots(api_token, id_user):
    cursor = con.cursor()
    Bots = cursor.execute(f"SELECT * FROM Bots WHERE api_key = '{api_token}'").fetchone()
    if not Bots:
        cursor.execute(f"INSERT INTO Bots (api_key, id_user) VALUES ('{api_token}', '{id_user}')")
        con.commit()
        return True
    else:
        return False


async def AllBotsForUser(id_user):
    cursor = con.cursor()
    Bots = cursor.execute(f"SELECT * FROM Bots WHERE id_user = '{id_user}'").fetchall()
    return Bots


async def DeleteBot(api_key):
    cursor = con.cursor()
    cursor.execute(f"DELETE FROM Bots WHERE api_key = '{api_key}'")
    con.commit()


async def Refund(id):
    cursor = con.cursor()
    cursor.execute(f'''UPDATE orders SET refund = 1 WHERE id = '{id}' ''')
    con.commit()


async def GetRefundStatus(id):
    cursor = con.cursor()
    Status = cursor.execute(f'''SELECT refund FROM orders WHERE id = '{id}' ''').fetchone()[0]
    return Status


async def WriteOffTheReferral(referral_id, sum_referral):
    cursor = con.cursor()
    cursor.execute(f'''UPDATE Referral SET referral_money = referral_money - '{sum_referral}' WHERE user_id = '{referral_id}' ''')
    con.commit()