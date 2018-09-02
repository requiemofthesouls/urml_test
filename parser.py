import os
import sqlite3
from json import load
from re import search
from urllib.parse import urlparse
from urllib.request import urlopen


def get_country_by_ip(ip: str) -> str:
    """ Возвращает страну по IP"""
    url = 'http://ipinfo.io/json'
    response = urlopen(url)
    data = json.load(response)
    IP = data['ip']
    org = data['org']
    city = data['city']
    country = data['country']
    region = data['region']
    return country


def get_params_from_querystring(querystring: str) -> dict:
    params = querystring.split('&')
    query = {}
    for param in params:
        key, value = param.split('=')[0], param.split('=')[1]
        query[key] = value
    return query


if __name__ == '__main__':
    CURRENT_DIR = os.getcwd()
    db_name = "usml.sqlite"
    logs_file = 'logs.txt'
    domain = 'https://all_to_the_bottom.com'

    conn = sqlite3.connect(os.path.join(CURRENT_DIR, db_name))
    cursor = conn.cursor()

    # Создание таблиц
    # cursor.executescript(
    #     """
    #         CREATE TABLE [Transaction] (
    #             id   INTEGER   PRIMARY KEY ASC AUTOINCREMENT,
    #             Time DATETIME,
    #             User TEXT (50) REFERENCES User (id),
    #             Goods_id CHAR (50),
    #             Amount CHAR (50),
    #             Cart_id CHAR (50),
    #             Pay_user_id CHAR (50),
    #             Success_pay BOOLEAN);
    #
    #         CREATE TABLE [Action] (
    #             id   INTEGER   PRIMARY KEY ASC AUTOINCREMENT,
    #             Time DATETIME,
    #             User TEXT (50) REFERENCES User (id),
    #             Category TEXT (50) REFERENCES Category (id),
    #             Goods TEXT (50) REFERENCES Goods (id));
    #
    #         CREATE TABLE Goods (
    #             id       INTEGER   PRIMARY KEY ASC AUTOINCREMENT
    #                                NOT NULL,
    #             Name     CHAR (50),
    #             Category TEXT (50)      REFERENCES Category (id));
    #
    #         CREATE TABLE User (
    #             id      INTEGER   PRIMARY KEY ASC AUTOINCREMENT
    #                               NOT NULL,
    #             IP      TEXT (20) UNIQUE,
    #             Country TEXT (50));
    #
    #         CREATE TABLE Category (
    #             id       INTEGER   PRIMARY KEY ASC AUTOINCREMENT,
    #             Category TEXT (50) UNIQUE);
    #     """)

    # Заполнение таблиц
    with open(os.path.join(CURRENT_DIR, logs_file), 'r') as f:
        for line in f:
            # Ищет дату формата 2018-08-01 00:07:54
            date = search(r'\d\d\d\d-\d\d-\d\d\s\d\d:\d\d:\d\d', line).group(0)
            # 192.168.1.1
            ip = search(r'[0-9]+(?:\.[0-9]+){3}', line).group(0)
            # Ищет урл и разбирает его параметры
            url = search("(?P<url>https?://[^\s]+)", line).group("url")
            url_details = urlparse(url)

            # print(date, ip, url_details, end='\n')

            if url_details.path == '/cart':
                query = get_params_from_querystring(url_details.query)
                print(date, ip, domain, url_details.path, query)

            elif url_details.path == '/pay':
                query = get_params_from_querystring(url_details.query)
                print(date, ip, domain, url_details.path, query)

            elif url_details.path[:12] == '/success_pay':
                success_pay_id = url_details.path.split('_')[-1][:-1]
                print(date, ip, domain, url_details.path, success_pay_id)
            else:
                # Извлекаем категорию и товар из урла
                category_and_product = url_details.path.split('/')
                # Удаляем пустые разделители из списка
                category_and_product.remove('')
                category_and_product.remove('')

                # Пробуем разделить категорию и товар в разные переменные
                # Если в логе нет записей про товар, записываем как Main Page
                if category_and_product:
                    category = category_and_product[0]
                    try:
                        product = category_and_product[1]
                    except IndexError:
                        product = None
                    print(date, ip, domain, url_details.path, category, product)
                else:
                    category_and_product = 'Main Page'
                    print(date, ip, domain, url_details.path, category_and_product)

            # cursor.execute(
            #     """
            #
            #     """
            # )

            conn.commit()

    conn.close()
