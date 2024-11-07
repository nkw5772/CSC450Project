import mysql.connector
import sqlite3

# Keeping old code for if/when we switch back to MySQL
'''
mydb = mysql.connector.connect(
    host="inventory450.ctq4yuwac5s0.us-east-2.rds.amazonaws.com",
    user="admin",
    password="450Database!",
    database="mysql"
)

if mydb.is_connected():
    print("Connected . . .\n")

mycursor = mydb.cursor()
'''

# Set up connection to database (cursor is used to interact with it)
database = sqlite3.connect('restaurant.db')
cursor = database.cursor()

# Command for adding account
add_account_command = ("INSERT INTO Account (AccountFN, AccountLN, AccountType, AccountEmail, AccountPhoneNo, AccountCreatedDate, PasswordHash) " \
                "VALUES (?, ?, ?, ?, ?, ?, ?)")
account_data = ("Jude", "Vargas", "Employee", "jrv4914@uncw.edu", "3143243173", "2024-10-30", "7e1271b650ade8c137425097c5d4268792cfef57503cf1b21fe21171045f3994")

login_query = ("SELECT AccountEmail, PasswordHash FROM Account WHERE AccountEmail = ?")
login_data = ("jrv4914@uncw.edu",) # Query parameters need to be in the form of a tuple, so the comma at the end of this line is necessary

cursor.execute(login_query, login_data)
database.commit()
print(cursor.fetchall())


# More old code
'''
for (account_email, password_hash) in mycursor:
    print(account_email, password_hash)

try:
    mycursor.execute(add_account_command, account_data)
    mydb.commit()
    print("LET'S GOOO!!!!")
except Exception as e:
    print("It fucked up.\n", e)
'''

# Close database connection when finished
cursor.close()

# Maybe add functions to call from app.py to abstract the process away from SQL statements
# def add_account(first_name: str, last_name: str, etc):