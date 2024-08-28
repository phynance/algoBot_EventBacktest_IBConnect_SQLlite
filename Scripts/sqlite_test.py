import sqlite3
import os

conn = sqlite3.connect("alpha.db")

cur = conn.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS people
        (first_name TEXT, last_name TEXT)''')


names_list = [
    ("Roderick", "Watson"),
    ("Roger", "Hom"),
    ("Petri", "Halonen"),
    ("Jussi", ""),  # Assuming "Jussi" has no last name
    ("James", "McCann")
]

cur.executemany('''
    INSERT INTO people (first_name, last_name) VALUES (?,?)
    ''', names_list)
conn.commit()

cur.close()
conn.close()
