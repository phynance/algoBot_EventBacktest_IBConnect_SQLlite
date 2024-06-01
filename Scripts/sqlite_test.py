import sqlite3
import os

# Specify the database filename
db_filename = 'IBportfolio.db'

# Connect to the database
connection = sqlite3.connect(db_filename)

# Get the absolute path of the database file
db_path = os.path.abspath(db_filename)
print(f"The database is located at: {db_path}")

# Remember to close the connection when done
connection.close()
connection = sqlite3.connect('mydatabase.db')
#
# # Create a table
# connection.execute('''
#     CREATE TABLE books (
#         id INTEGER PRIMARY KEY,
#         title TEXT,
#         author TEXT,
#         year INTEGER
#     )
# ''')
#
# connection.execute("INSERT INTO books (title, author, year) VALUES (?, ?, ?)", ("The Great Gatsby", "F. Scott Fitzgerald", 1925))
#
# # Query data from the table
# result = connection.execute("SELECT * FROM books")
# data = result.fetchall()
#
# # Process the retrieved data
# for row in data:
#     print(row)
#
# connection.close()
