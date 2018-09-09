import os
import sqlite3

from pprint import pprint

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
    frozen_fish_id = cursor.execute("SELECT Category.id FROM Category WHERE Category.Category='frozen_fish'").fetchone()
    records = cursor.execute(
        """
            SELECT Action.Time
            FROM Action
            WHERE Action.Category = ?
        """, frozen_fish_id).fetchall()
    print(records)


time_analytics_for_frozen_fish_category()


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
