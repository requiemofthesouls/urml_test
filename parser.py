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
            CREATE TABLE [Transaction] (
                id   INTEGER   PRIMARY KEY ASC AUTOINCREMENT,
                Time DATETIME,
                User INTEGER REFERENCES User (id),
                Goods_id CHAR (50),
                Amount CHAR (50),
                Cart_id CHAR (50),
                Pay_user_id CHAR (50),
                Success_pay BOOLEAN);

            CREATE TABLE [Action] (
                id   INTEGER   PRIMARY KEY ASC AUTOINCREMENT,
                Time DATETIME,
                User TEXT (50) REFERENCES User (id),
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
            date = search(r'(\d{4}-\d{2}-\d{2})\s(\d{2}:\d{2}:\d{2})', line).group(0)
            # 192.168.1.1
            ip = search(r'[0-9]+(?:\.[0-9]+){3}', line).group(0)
            # Ищет урл
            url = search(r'(?P<url>https?://[^\s]+)', line).group("url")
            # Разбирает его параметры
            url_details = urlparse(url)

            # print(date, ip, url_details, end='\n')

            if url_details.path == '/cart':
                query = parse_qs(url_details.query)
                records = (ip, gi.country_name_by_addr(ip))
                cursor.execute(
                    """
                        INSERT OR IGNORE INTO User (IP, Country)
                        VALUES (?, ?)
                    """, records)
                # print(date, ip, domain, url_details.path, query)

            elif url_details.path == '/pay':
                query = parse_qs(url_details.query)
                records = (ip, gi.country_name_by_addr(ip))
                cursor.execute(
                    """
                        INSERT OR IGNORE INTO User (IP, Country)
                        VALUES (?, ?)
                    """, records)
                # print(date, ip, domain, url_details.path, query)

            elif url_details.path[:12] == '/success_pay':
                success_pay_id = url_details.path.split('_')[-1][:-1]
                records = (ip, gi.country_name_by_addr(ip))
                cursor.execute(
                    """
                        INSERT OR IGNORE INTO User (IP, Country)
                        VALUES (?, ?)
                    """, records)

                # print(date, ip, domain, url_details.path, success_pay_id)

            else:
                # Извлекаем категорию и товар из урла
                category_and_product = url_details.path.split('/')
                # Удаляем пустые разделители из списка
                category_and_product.remove('')
                category_and_product.remove('')
                records = (ip, gi.country_name_by_addr(ip))

                # Пробуем разделить категорию и товар в разные переменные
                # Если в логе нет записей про товар, записываем как Main Page
                if category_and_product:
                    category = (category_and_product[0],)

                    cursor.execute(
                        """
                            INSERT OR IGNORE INTO Category (Category)
                            VALUES (?)
                        """, category)

                    # Ищет id категории в базе
                    category_id = cursor.execute(
                        """
                            SELECT id FROM Category
                            WHERE Category=?
                        """, category).fetchone()

                    try:
                        product = category_and_product[1]
                    except IndexError:
                        product = 'None'

                    # Заполняем таблицу "Товары"
                    values = (product, category_id[0])
                    cursor.execute(
                        """
                            INSERT INTO Goods (Name, Category)
                            VALUES (?, ?)
                        """, values)

                    cursor.execute(
                        """
                            INSERT OR IGNORE INTO User (IP, Country)
                            VALUES (?, ?)
                        """, records)

                    goods_id = cursor.execute("SELECT id FROM Goods WHERE (Name, Category)=(?, ?)", values).fetchone()
                    user_id = cursor.execute("""SELECT id FROM User WHERE IP=(?)""", (ip, )).fetchone()

                    values = (date, user_id[0], category_id[0], goods_id[0])
                    cursor.execute(
                        """
                            INSERT INTO Action (Time, User, Category, Goods)
                            VALUES (?, ?, ?, ?)
                        """, values)
                    print('Action from {}, User: {}, Path: {}, Category: {}, Product: {}'.format(
                        date, ip, url_details.path, category, product))
                else:
                    category_and_product = 'Main Page'
                    # Если пользователь посещал главную то не записываем ничего.
                    cursor.execute(
                        """
                            INSERT OR IGNORE INTO User (IP, Country)
                            VALUES (?, ?)
                        """, records)

                    user_id = cursor.execute("""SELECT id FROM User WHERE IP=(?)""", (ip, )).fetchone()
                    # category, goods = None, None

                    # Заполняем информацию о действии пользователя
                    values = (date, user_id[0])
                    cursor.execute(
                        """
                            INSERT INTO Action (Time, User)
                            VALUES (?, ?)
                        """, values)

                    print('Action from {}, User: {}, Path: {}, Visited goods: {}'.format(
                        date, ip, url_details.path, category_and_product))

            conn.commit()

    conn.close()
