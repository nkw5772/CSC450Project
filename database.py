import mysql.connector
import sqlite3

class Database:
    """
    Helper class for database interactions
    Life Pro Tip: single-value parameters still need to be in Tuple form, so assign a parameter value as (param_name,)
    """

    def __init__(self):
        # Set up connection to database (cursor is used to interact with it)
        try:
            self.database = sqlite3.connect('restaurant.db')
        except sqlite3.Error as error:
            raise Exception('Was not able to establish a connection to the database.\n', error)
        self.cursor = self.database.cursor()
    
    def __del__(self):
        self.cursor.close()


    def email_is_unique(self, email: str) -> bool:
        command = "SELECT COUNT(*) FROM Account WHERE AccountEmail = ?"
        params = (email,)
        self.cursor.execute(command, params)
        if self.cursor.fetchone()[0] <= 0: # Returns a tuple, so gotta index to get value
            return True
        return False
        # Could also be done by (SELECT * FROM Account) & using cursor.rowcount - not sure which way is better

    def phone_is_unique(self, phone: str) -> bool:
        command = "SELECT COUNT(*) FROM Account WHERE AccountPhoneNo = ?"
        params = (phone,)
        self.cursor.execute(command, params)
        if self.cursor.fetchone()[0] <= 0:
            return True
        return False

    def check_in_search(self, last_name: str):
        command = "SELECT a.AccountFN, a.AccountLN, r.ResNoGuests, r.TableID FROM Account a, Reservation r WHERE r.ResOwner = a.AccountID AND AccountLN = ?"
        params = (last_name,)
        self.cursor.execute(command, params)
        if self.cursor.rowcount <= 0:
            return None
        return self.cursor.fetchall()

    def add_account(self, first_name: str, last_name: str, type: str, email: str, phone: str, created_date: str, password: str):
        command = "INSERT INTO Account (AccountFN, AccountLN, AccountType, AccountEmail, AccountPhoneNo, AccountCreatedDate, PasswordHash) " \
                    "VALUES (?, ?, ?, ?, ?, ?, ?)"
        params = (first_name, last_name, type, email, phone, created_date, password)
        self.cursor.execute(command, params)
        self.database.commit()
    # INSERT INTO Reservation (ResDate, ResTime, ResNoGuests, TimeCreated, TimeUpdated, ResStatus, TableID, ResOwner)
    # VALUES ("2024-11-12", "00:04:00", 3, "08:23:42", "08:23:42", "Ready", 1, 1)
    # def verify_exists(self, email):
    #     self.cursor.execute("SELECT PasswordHash FROM Account WHERE AccountEmail = ?", (email,))
    
    #     # Fetch the result
    #     result = self.cursor.fetchone()
    
    #     # Check if the email exists in the database
    #     if result is None:
    #     # Email does not exist, return False
    #         return False
    
    def verify_login(self, email, password):
        
        self.cursor.execute("SELECT PasswordHash FROM Account WHERE AccountEmail = ?", (email,))
        
        result = self.cursor.fetchone()
        if result is None:
            return False
        if result[0] == password:
            return True
        return False
        

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