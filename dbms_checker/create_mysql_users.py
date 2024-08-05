# -*- coding: utf-8 -*-

import mysql.connector

cnx = mysql.connector.connect(
    host='localhost',
    user='root',
    password='password',
)
cursor = cnx.cursor()
for idx in range(100):
    try:
        cursor.execute(f"CREATE USER 'yang{idx}'@'localhost' IDENTIFIED BY 'password';")
        cursor.execute(f"CREATE DATABASE test{idx}")
    except Exception as err:
        print(err)
    cursor.execute(f"GRANT ALL PRIVILEGES ON *.* TO 'yang{idx}'@'localhost';")
    cursor.execute("FLUSH PRIVILEGES;")
    print(cursor.description)
