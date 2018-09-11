import os
import sqlite3

from re import search

CURRENT_DIR = os.getcwd()
db_name = "usml.sqlite"

conn = sqlite3.connect(os.path.join(CURRENT_DIR, db_name))
cursor = conn.cursor()


def test_divider(number):
    return print('-' * 46 + 'Test # %s' % number + '-' * 46)


# 1
def test_most_of_the_action():
    test_divider(1)
    actions = dict(cursor.execute(
        """
            SELECT User.Country AS "Country",
            COUNT(User.Country) AS "Amount of users"
            FROM Action 
                JOIN User ON Action.User = User.id
            WHERE User.Country != ''
            GROUP BY Country
            ORDER BY "Amount of users" DESC
        """).fetchall())
    carts = dict(cursor.execute(
        """
            SELECT User.Country AS "Country",
            COUNT(User.Country) AS "Amount of users"
            FROM Cart
                JOIN User ON Cart.User = User.id
            WHERE User.Country != ''
            GROUP BY Country
            ORDER BY "Amount of users" DESC
        """).fetchall())
    purchases = dict(cursor.execute(
        """
            SELECT User.Country AS "Country",
            COUNT(User.Country) AS "Amount of users"
            FROM Purchase
                JOIN User ON Purchase.User = User.id
            WHERE User.Country != ''
            GROUP BY Country
            ORDER BY "Amount of users" DESC
        """).fetchall())
    for key in actions:
        if carts.get(key):
            actions[key] += carts.get(key)
        if purchases.get(key):
            actions[key] += purchases.get(key)
    all_actions_sorted = sorted(actions.items(), key=lambda x: x[1], reverse=True)
    print('Больше всего действий на сайте (%s) совершили пользователи из страны %s' % (
        all_actions_sorted[0][1], all_actions_sorted[0][0]))


test_most_of_the_action()


# 2
def test_goods_from_category_fresh_fish():
    test_divider(2)
    fresh_fish_id = cursor.execute("SELECT Category.id FROM Category WHERE Category.Category='fresh_fish'").fetchone()
    records = cursor.execute(
        """
            SELECT User.Country, COUNT() AS "Amount"
            FROM User
                JOIN Action ON Action.User = User.id
            WHERE User.Country != '' AND Action.Category = ?
            GROUP BY User.Country
            ORDER BY "Amount" DESC
        """, fresh_fish_id).fetchall()
    print('Товарами из категории fresh_fish больше всего интересовались пользователи из страны %s (%s раз)' % (
        records[0][0], records[0][1]))


test_goods_from_category_fresh_fish()


# 3
def time_analytics_for_frozen_fish_category():
    test_divider(3)
    records = cursor.execute(
        """
            SELECT Action.Time
            FROM Action
            WHERE Action.Time BETWEEN DATETIME('2018-08-01 00:00') AND ('now')
              AND Action.Category = (SELECT Category.id FROM Category WHERE Category.Category = 'frozen_fish')
        """).fetchall()
    night_hours = ('00', '01', '02', '03', '04', '05')
    morning_hours = ('06', '07', '08', '09', '10', '11')
    afternoon_hours = tuple(str(x) for x in range(12, 18))
    evening_hours = tuple(str(x) for x in range(18, 24))
    stats = dict(night=0, morning=0, afternoon=0, evening=0)
    for date in records:
        time = date[0].split(' ')[1]
        hours = time[:2]
        if hours in night_hours:
            stats['night'] += 1
        elif hours in morning_hours:
            stats['morning'] += 1
        elif hours in evening_hours:
            stats['evening'] += 1
        elif hours in afternoon_hours:
            stats['afternoon'] += 1
    print('Категорию frozen_fish чаще всего просматривают в %s' %
          sorted(stats.items(), key=lambda x: x[1], reverse=True)[0][0])


time_analytics_for_frozen_fish_category()


# 4
def max_queries_per_hour():
    test_divider(4)
    queries = {}
    records = cursor.execute(
        """
            SELECT Action.Time
            FROM Action
                UNION ALL
            SELECT Cart.Time
            FROM Cart
                UNION ALL
            SELECT Purchase.Time
            FROM Purchase
                UNION ALL
            SELECT Success_Pay.Time
            FROM Success_Pay
        """).fetchall()
    for record in records:
        date = record[0].split(' ')[0]
        time = record[0].split(' ')[1]
        hours = time[:2]
        key = date + '-' + hours + 'h'
        try:
            queries[key] += 1
        except KeyError:
            queries[key] = 1
    queries_sorted = sorted(queries.items(), key=lambda x: x[1], reverse=True)[0]
    print('Максимальное количество запросов за час (%s) в %s' % (queries_sorted[1], queries_sorted[0]))


max_queries_per_hour()


# 5
def the_best_selling_with_semi_manufactures():
    test_divider(5)
    analytics = {}
    carts_with_semi_manufactures = cursor.execute(
        """
            SELECT DISTINCT Cart.Cart_id
            FROM Cart
            WHERE Cart.Success_pay = 1
              AND Cart.Goods_id IN (SELECT Goods.querystring_id
                                    FROM Goods
                                    WHERE Goods.Category =
                                    (SELECT Category.id
                                     FROM Category
                                     WHERE Category.Category = 'semi_manufactures'))
            ORDER BY Cart_id
        """).fetchall()
    for cart in carts_with_semi_manufactures:
        cart_id = cart[0]
        records = cursor.execute('SELECT Cart.Goods_id, Cart.Amount FROM Cart WHERE Cart.Cart_id = (?)', cart).fetchall()
        for goods in records:
            goods_qs_id = goods[0]
            amount = goods[1]
            category_id = cursor.execute('SELECT Goods.Category FROM Goods WHERE querystring_id = (?)', (goods_qs_id, )).fetchone()
            key = cursor.execute('SELECT Category.Category FROM Category WHERE Category.id = (?)', category_id).fetchone()[0]
            try:
                analytics[key] += amount
            except KeyError:
                analytics[key] = amount
    sorted_analytics = sorted(analytics.items(), key=lambda x: x[1], reverse=True)
    print('Совместно с полуфабрикатами покупают товары из категорий: %s' % (sorted_analytics[1:]))

    # print(records)


the_best_selling_with_semi_manufactures()


# 6
def unpaid_carts():
    test_divider(6)
    amount = cursor.execute(
        """
            SELECT COUNT(*)
            FROM (SELECT DISTINCT Cart.Cart_id FROM Cart WHERE Cart.Success_pay ISNULL)
        """).fetchone()[0]
    print('Количество неоплаченных тележек: %s' % amount)


unpaid_carts()


# 7
def repeat_purchases():
    test_divider(7)
    amount = cursor.execute(
        """
            SELECT COUNT(*)
            FROM (SELECT Purchase.Cart_id, User.IP, COUNT(User.IP) AS "Purchases"
                  FROM User
                         JOIN Purchase ON Purchase.User = User.id
                  GROUP BY User.IP
                  HAVING Purchases > 1
                  ORDER BY "Purchases" DESC)
        """).fetchone()[0]
    print("Количество пользователей, совершившие более одной покупки: %s" % amount)


repeat_purchases()

conn.close()
