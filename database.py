import mysql.connector

mydb = mysql.connector.connect(
    host="inventory450.ctq4yuwac5s0.us-east-2.rds.amazonaws.com",
    user="admin",
    password="450Database!",
    database="mysql"
)

if mydb.is_connected():
    print("Connected . . .\n")

mycursor = mydb.cursor()

# Command for adding account
add_account_command = ("INSERT INTO Accounts (AccountFN, AccountLN, AccountType, AccountEmail, AccountPhoneNo, AccountCreatedDate, PasswordHash) " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)")

account_data = ("Jude", "Vargas", "Employee", "jrv4914@uncw.edu", "3143243173", "2024-10-30", "7e1271b650ade8c137425097c5d4268792cfef57503cf1b21fe21171045f3994")

try:
    mycursor.execute(add_account_command, account_data)
    mydb.commit()
    print("LET'S GOOO!!!!")
except Exception as e:
    print("It fucked up.\n", e)