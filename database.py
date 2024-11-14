import mysql.connector
import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

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
        command = """
        SELECT COUNT(*) 
        FROM Account 
        WHERE AccountPhoneNo = ?
        """
        params = (phone,)
        self.cursor.execute(command, params)
        if self.cursor.fetchone()[0] <= 0:
            return True
        return False

    def check_in_search(self, last_name: str):
        command = """
        SELECT a.AccountFN, a.AccountLN, r.ResNoGuests, r.TableID 
        FROM Account a, Reservation r 
        WHERE r.ResOwner = a.AccountID AND AccountLN = ?
        """
        params = (last_name,)
        self.cursor.execute(command, params)
        results = self.cursor.fetchall()
        if len(results) <= 0:
            return None
        return results
    
    def make_reservation(self, ResDate, ResTime, ResNoGuests, TableID):
        ResID = 1 # Temporary hard code
        TimeCreated = datetime.now()
        TimeUpdated = TimeCreated
        ResStatus = "Pending" # Idk the different status' so open to change
        ResOwner = "Nathan" # Temporary hard code until we can figure out how to get the name from the cookie
        create_reservation = """
        INSERT INTO Reservation (ResID, ResDate, ResTime, ResNoGuests, TimeCreated, TimeUpdated, ResStatus, TableID, ResOwner)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.cursor.execute(create_reservation, (ResID, ResDate, ResTime, ResNoGuests, TimeCreated, TimeUpdated, ResStatus, TableID, ResOwner))
        self.database.commit()


 # Check-in a reservation by updating both Reservation and Seating tables
    def check_in_reservation(self, reservation_id):
        try:
            update_reservation = """
            UPDATE Reservation
            SET ResStatus = 'checked_in'
            WHERE ResID = ?;
            """
            self.cursor.execute(update_reservation, (reservation_id,))
            print("Updated Reservation table for ResID:", reservation_id)

            update_seating = """
            UPDATE Seating
            SET CurrentReservation = ?
            WHERE TableID = (SELECT TableID FROM Reservation WHERE ResID = ?);
            """
            self.cursor.execute(update_seating, (reservation_id,))
            print("Updated Seating table for TableID linked to ResID:", reservation_id)

            self.database.commit()
            print("Database commit successful for check-in operation.")
            return True
        except sqlite3.Error as e:
            print("Error checking in reservation:", e)
            self.database.rollback()
            return False
    
    # This is kinda a guess until we get a proper ordering page up
    # Still need to figure out how we are gunna do expiration date and stuff, maybe make a file for holding each item data?
    def order_meat(self, item, quantity):
        query = """
        INSERT INTO Inventory (Item, Quantity)
        VALUES (?, ?)
        """
        self.cursor.execute(query, (item, quantity))
        self.database.commit()


    def add_account(self, first_name: str, last_name: str, type: str, email: str, phone: str, created_date: str, password: str):
        command = """
        INSERT INTO Account (AccountFN, AccountLN, AccountType, AccountEmail, AccountPhoneNo, AccountCreatedDate, PasswordHash) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """ 
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
    
    def verify_login(self, email, password): # Maybe add extra check for phone number to sign in with either?
        
        self.cursor.execute("SELECT PasswordHash FROM Account WHERE AccountEmail = ?", (email,))
        
        result = self.cursor.fetchone()
        if result is None:
            return False
        if result[0] == password:
            return True
        return False
        
    def get_account_type(self, email: str) -> str:
        command = "SELECT AccountType FROM Account WHERE AccountEmail = ?"
        params = (email,)
        self.cursor.execute(command, params)
        return self.cursor.fetchone()[0]

    def remind_reservations(self): # pw: csc team 2
        command = """SELECT a.AccountEmail, a.AccountFN, r.ResTime
                     FROM Account a, Reservation r
                     WHERE a.AccountID = r.ResOwner
                     AND r.ResStatus = "ready"
                     AND r.ResDate = ?
                     AND r.ResTime < ?
                 """
        today = datetime.today().strftime('%Y-%m-%d')
        remind_threshold = (datetime.now() + timedelta(minutes=30)).strftime('%H:%M"%S')
        self.cursor.execute(command, (today, remind_threshold))

        for row in self.cursor.fetchall():
            subject = 'Your reservation is almost here!'
            body = f"""Hello {row[1]}!
                       Your reservation at {row[2]} is almost here.
                       Don't miss your reservation!!!
                """
            self.send_email(row[0], subject, body)

    def send_email(self, recipient_address, subject, body):
        # Gmail SMTP server setup
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        email = "judevargas22@gmail.com"
        app_password = "vits bave zyna htfl"

        alias_email = "csc450project2024@gmail.com"

        message = MIMEMultipart()
        message['From'] = alias_email
        message['To'] = recipient_address
        message["Subject"] = subject
        message.attach(MIMEText(body, 'plain'))

        # Connect to Gmail SMTP server
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email, app_password)
            server.sendmail(alias_email, recipient_address, message.as_string())  # Send with alias
            print("Email sent successfully from alias!")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            server.quit()


    def handle_no_shows(self):
        command = """UPDATE Reservation
                 SET ResStatus = "no_show"
                 WHERE ResDate < ? OR (ResDate = ? AND ResTime < ?)
                 """

        # Keep this at the very end of this function
        self.database.commit()
    
    def unreserve_table(self, reservation_id):
        command = """UPDATE Seating
                            SET CurrentReservation = NULL
                            WHERE TableID = (SELECT TableID FROM Reservation WHERE ResID = ?);
                            """
        params = (reservation_id,)
        self.cursor.execute(command, params)
        self.database.commit()
        

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