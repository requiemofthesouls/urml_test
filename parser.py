import os
import sqlite3
from re import search
from urllib.parse import urlparse, parse_qs
from urllib.request import urlopen

from pygeoip import GeoIP

if __name__ == '__main__':
    CURRENT_DIR = os.getcwd()
    db_name = "usml.sqlite"
    try:
        os.remove(os.path.join(CURRENT_DIR, db_name))
    except FileNotFoundError:
        pass
    logs_file = 'logs.txt'
    domain = 'https://all_to_the_bottom.com'

    gi = GeoIP(os.path.join(CURRENT_DIR, 'GeoIP.dat'))

    conn = sqlite3.connect(os.path.join(CURRENT_DIR, db_name))
    cursor = conn.cursor()

    # Создание таблиц
    cursor.executescript(
        """
            CREATE TABLE Cart (
                id   INTEGER   PRIMARY KEY ASC AUTOINCREMENT,
                Time DATETIME,
                User INTEGER REFERENCES User (id),
                Goods_id INTEGER,
                Amount INTEGER,
                Cart_id INTEGER,
                Success_pay BOOLEAN);
                
            CREATE TABLE Purchase (
                id   INTEGER   PRIMARY KEY ASC AUTOINCREMENT,
                Time DATETIME,
                User INTEGER REFERENCES User (id),
                Cart_id INTEGER REFERENCES Cart (id),
                Pay_user_id INTEGER);

            CREATE TABLE Action (
                id   INTEGER   PRIMARY KEY ASC AUTOINCREMENT,
                Time DATETIME,
                User INTEGER REFERENCES User (id),
                Category INTEGER REFERENCES Category (id),
                Goods INTEGER REFERENCES Goods (id));

            CREATE TABLE Goods (
                id       INTEGER   PRIMARY KEY ASC AUTOINCREMENT,
                Name     TEXT (50),
                Category INTEGER      REFERENCES Category (id));

            CREATE TABLE User (
                id      INTEGER   PRIMARY KEY ASC AUTOINCREMENT,
                IP      TEXT (20) UNIQUE,
                Country TEXT (50));

            CREATE TABLE Category (
                id       INTEGER   PRIMARY KEY ASC AUTOINCREMENT,
                Category TEXT (50) UNIQUE);
        """)

    # Заполнение таблиц
    with open(os.path.join(CURRENT_DIR, logs_file), 'r') as f:
        for line in f:
            # Ищет дату формата 2018-08-01 00:07:54
            date = search(r'\d{4}(-\d{2})+\s\d{2}(:\d{2})+', line).group(0)
            # 192.168.1.1
            ip = search(r'[0-9]+(?:\.[0-9]+){3}', line).group(0)
            # Ищет урл
            url = search(r'(?P<url>https?://[^\s]+)', line).group("url")
            # Разбирает его параметры
            url_details = urlparse(url)
            # Вставляем запись о пользователе
            user_info = (ip, gi.country_name_by_addr(ip))
            cursor.execute("INSERT OR IGNORE INTO User (IP, Country) VALUES (?, ?)", user_info)
            # Берем из базы его id
            user_id = cursor.execute("SELECT id FROM User WHERE IP=(?)", (ip,)).fetchone()[0]

            if url_details.path == '/cart':
                # Разбираем параметры из querystring
                query = parse_qs(url_details.query)
                goods_id = query['goods_id'][0]
                amount = query['amount'][0]
                cart_id = query['cart_id'][0]
                # Вставляем в базу запись о тележке
                values = (date, user_id, goods_id, amount, cart_id)
                cursor.execute("INSERT INTO Cart (Time, User, Goods_id, Amount, Cart_id) VALUES (?, ?, ?, ?, ?)", values)
                print('Cart from: {}, User: {}, Path: {}, Inserted values: {}'.format(date, ip, url_details.path, query))

            elif url_details.path == '/pay':
                # Разбираем параметры из querystring
                query = parse_qs(url_details.query)
                user_qs_id = query['user_id'][0]
                cart_qs_id = query['cart_id'][0]
                # Ищем тележку с нужным нам id
                cart_id = cursor.execute("SELECT id FROM Cart WHERE Cart_id=?", (cart_qs_id, )).fetchone()[0]
                # Вставляем запись об оплате
                values = (date, user_id, cart_id, user_qs_id)
                cursor.execute("INSERT INTO Purchase (Time, User, Cart_id, Pay_user_id) VALUES (?, ?, ?, ?)", values)
                print('Pay from: {}, User: {}, Path: {}, Cart id: {}, User id: {}'.format(date, ip, url_details.path, cart_qs_id, user_id))

            elif url_details.path[:12] == '/success_pay':
                success_pay_id = url_details.path.split('_')[-1][:-1]
                # Ищем тележки с нужным id
                purchase_id = cursor.execute('SELECT id FROM Cart WHERE Cart_id=?', (success_pay_id, )).fetchall()
                # Обновляем поле о успешной оплате тележки.
                for id_ in purchase_id:
                    cursor.execute('UPDATE Cart SET Success_pay=(?) WHERE id=(?)', (True, id_[0]))
                    print('Success pay for cart №: {}, User: {}, Time: {}'.format(id_[0], ip, date))

            else:
                # Извлекаем категорию и товар из урла
                category_and_product = url_details.path.split('/')
                # Удаляем пустые разделители из списка
                category_and_product.remove('')
                category_and_product.remove('')
                # Пробуем разделить категорию и товар в разные переменные
                # Если в логе нет записей про товар, записываем как Main Page
                if category_and_product:
                    # Символьное представление категории
                    category = (category_and_product[0],)  # frozen_fish
                    # Вставляем категорию если её нет и запоминаем её id
                    cursor.execute("INSERT OR IGNORE INTO Category (Category) VALUES (?)", category)
                    category_id = cursor.execute("SELECT id FROM Category WHERE Category=?", category).fetchone()[0]

                    try:
                        product = category_and_product[1]
                        values = (product, category_id)
                        # Заполняем таблицу "Товары" категорией и товаром и запоминаем id товара
                        try:
                            goods_id = cursor.execute("SELECT id FROM Goods WHERE (Name, Category)=(?, ?)", values).fetchone()[0]
                        except TypeError:
                            cursor.execute("INSERT INTO Goods (Name, Category) VALUES (?, ?)", values)
                            goods_id = cursor.execute("SELECT id FROM Goods WHERE (Name, Category)=(?, ?)", values).fetchone()[0]
                        # Заполняем действия
                        values = (date, user_id, category_id, goods_id)
                        cursor.execute("INSERT INTO Action (Time, User, Category, Goods) VALUES (?, ?, ?, ?)", values)
                        print('Action from {}, User: {}, Path: {}, Category: {}, Product: {}'.format(
                            date, ip, url_details.path, category[0], product))

                    except IndexError:
                        # Категория есть, но нет товара.
                        product = None
                        # Заполняем только категорию.
                        values = (date, user_id, category_id)
                        cursor.execute("INSERT INTO Action (Time, User, Category) VALUES (?, ?, ?)", values)
                        print('Action from {}, User: {}, Path: {}, Category: {}'.format(
                            date, ip, url_details.path, category[0]))
                else:
                    category_and_product = 'Main Page'
                    # Если пользователь посещал главную то не записываем ничего в товар и категории.
                    # Заполняем информацию о действии пользователя.
                    values = (date, user_id)
                    cursor.execute("INSERT INTO Action (Time, User) VALUES (?, ?)", values)
                    print('Action from {}, User: {}, Path: {}, Visited: {}'.format(
                        date, ip, url_details.path, category_and_product))

            conn.commit()

    conn.close()
