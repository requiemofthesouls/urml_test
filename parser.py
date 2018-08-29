import sqlite3
from re import search


def get_unique_ip():
    """ Вытягивает ip-шники из лога, возвращает их уникальное множество. """
    users_ip = set()
    with open(path, 'r') as f:
        for line in f:
            ip = search(r'[0-9]+(?:\.[0-9]+){3}', line)
            users_ip.add(ip.group(0))
        return users_ip


if __name__ == '__main__':
    path = 'C:\logs.txt'
    users_ip = get_unique_ip()

    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()

    # Создание таблицы
    # cursor.execute("""CREATE TABLE Users
    #                 (title text)
    #             """)

    cursor.execute("""INSERT INTO Users 
    VALUES ('192.168.1.1')""")

    conn.commit()
