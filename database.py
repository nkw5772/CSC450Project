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

    ###
    #region DB CONNECTION
    ###
    def __init__(self):
        # Set up connection to database (cursor is used to interact with it)
        try:
            self.database = sqlite3.connect('restaurant.db')
        except sqlite3.Error as error:
            raise Exception('Was not able to establish a connection to the database.\n', error)
        self.cursor = self.database.cursor()
    
    def __del__(self):
        self.cursor.close()
    ###
    #endregion DB CONNECTION
    ###

    ###
    #region USER AUTHENTICATION
    ###

    def add_account(self, first_name: str, last_name: str, type: str, email: str, phone: str, created_date: str, password: str) -> None:
        command = """
        INSERT INTO Account (AccountFN, AccountLN, AccountType, AccountEmail, AccountPhoneNo, AccountCreatedDate, PasswordHash) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """ 
        params = (first_name, last_name, type, email, phone, created_date, password)
        self.cursor.execute(command, params)
        self.database.commit()

    def email_is_unique(self, email: str) -> bool:
        command = """
        SELECT COUNT(*)
        FROM Account
        WHERE AccountEmail = ?
        """
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
    
    def verify_login(self, email: str, password: str) -> bool: # Maybe add extra check for phone number to sign in with either?
        self.cursor.execute("SELECT PasswordHash FROM Account WHERE AccountEmail = ?", (email,))
        
        result = self.cursor.fetchone()
        if result is None:
            return False
        if result[0] == password:
            return True
        return False
        
    def get_account_type(self, email: str) -> str:
        command = """
        SELECT AccountType
        FROM Account
        WHERE AccountEmail = ?
        """
        params = (email,)
        self.cursor.execute(command, params)
        return self.cursor.fetchone()[0]
    
    def get_name_from_email(self, email: str) -> tuple:
        command = """
        SELECT AccountFN, AccountLN
        FROM Account
        WHERE AccountEmail = ?
        """
        params = (email,)
        self.cursor.execute(command, params)
        return self.cursor.fetchone()
    
    def get_id_from_email(self, email: str) -> int:
        command = """
        SELECT AccountID
        FROM Account
        WHERE AccountEmail = ?
        """
        params = (email,)
        self.cursor.execute(command, params)
        return self.cursor.fetchone()[0]

    ###
    #endregion USER AUTHENTICATION
    ###

    ###
    #region  RESERVATIONS
    ###
    def check_in_search(self, last_name: str) -> list | None:
        command = """
        SELECT a.AccountFN, a.AccountLN, r.ResNoGuests, r.TableID, r.ResID 
        FROM Account a, Reservation r 
        WHERE r.ResOwner = a.AccountID AND LOWER(a.AccountLN) = ?
        """
        params = (last_name.lower(),)
        self.cursor.execute(command, params)
        results = self.cursor.fetchall()
        if len(results) <= 0:
            return None
        return results
    
    def get_user_reservations(self, email: str) -> list | None:
        command = """
        SELECT r.ResDate, r.ResTime, r.ResNoGuests, r.TableID, r.ResID
        FROM Account a, Reservation r 
        WHERE r.ResOwner = a.AccountID
        AND a.AccountEmail = ?
        AND ResStatus IN ("scheduled", "ready", "checked_in", "finished")
        ORDER BY r.Resdate ASC, r.ResTime ASC
        """
        params = (email,)
        self.cursor.execute(command, params)
        results = self.cursor.fetchall()
        if len(results) <= 0:
            return None
        return results


 # Check-in a reservation by updating both Reservation and Seating tables
    def check_in_reservation(self, reservation_id):
        try:
            self.update_res_status(reservation_id, 'checked_in')
            print("Updated Reservation table for ResID:", reservation_id)

            update_seating = """
            UPDATE Seating
            SET CurrentReservation = ?
            WHERE TableID = (SELECT TableID FROM Reservation WHERE ResID = ?);
            """
            self.cursor.execute(update_seating, (reservation_id, reservation_id))
            print("Updated Seating table for TableID linked to ResID:", reservation_id)

            self.database.commit()
            print("Database commit successful for check-in operation.")
            return True
        except sqlite3.Error as e:
            print("Error checking in reservation:", e)
            self.database.rollback()
            return False

    def check_reservation_conflict(self, table_id, reservation_date, reservation_time):
        try:
            # Query for overlapping reservations (within an hour)
            query = """
            SELECT COUNT(*)
            FROM Reservation r
            JOIN ReservedSeats rs ON r.ResID = rs.ResID
            JOIN Seating s ON rs.TableID = s.TableID
            WHERE s.TableID = ?
            AND r.ResDate = ?
            AND (
                (r.ResTime <= ? AND DATETIME(r.ResTime, '+60 minutes') > ?)
                OR (r.ResTime >= ? AND DATETIME(?, '+60 minutes') > r.ResTime)
            )
            """
            self.cursor.execute(query, (table_id, reservation_date, reservation_time, reservation_time, reservation_time, reservation_time))
            result = self.cursor.fetchone()
            return result[0] > 0  # True if there is a conflicting reservation
        except Exception as e:
            print(f"Error checking reservation conflict: {e}")
            return True
        
    def make_reservation(self, reservation_date, reservation_time, guests, TimeCreated, TimeUpdated, ResStatus, table_ids, ResOwner):
        reserve_command = """
        INSERT INTO Reservation (ResDate, ResTime, ResNoGuests, TimeCreated, TimeUpdated, ResStatus, ResOwner)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        add_table_command = """
        INSERT INTO ReservedSeats (ResID, TableID)
        Values (?, ?)
        """
        params = (reservation_date, reservation_time, guests, TimeCreated, TimeUpdated, ResStatus, ResOwner)
        self.cursor.execute(reserve_command, params)

        reservation_id = self.cursor.lastrowid
        for table in table_ids:
            params = (reservation_id, table)
            self.cursor.execute(add_table_command, params)
        self.database.commit()

    def modify_reservation(self, reservation_id, reservation_date, reservation_time, guests, time_created, time_updated, res_status, table_ids, res_owner):
        modify_command = """
        UPDATE Reservation SET 
        ResDate = ?,
        ResTime = ?,
        ResNoGuests = ?,
        TimeCreated = ?,
        TimeUpdated = ?,
        ResStatus = ?,
        TableID = ?,
        ResOwner = ?
        WHERE ResID = ?
        """

        placeholders = ', '.join(['?'] * len(table_ids))
        remove_tables_command = f"""
        DELETE FROM ReservedSeats
        WHERE ResID = ? AND TableID NOT IN ({placeholders})
        """

        add_table_command = """
        INSERT INTO ReservedSeats (ResID, TableID)
        Values (?, ?)
        """
        # set new reservation
        params = (reservation_date, reservation_time, guests, time_created, time_updated, res_status, table, res_owner, reservation_id)
        self.cursor.execute(modify_command, params)
        # Remove old reserved tables
        params = (reservation_id, table_ids)
        self.cursor.execute(remove_tables_command, params)
        for table in table_ids:        
            # Add new tables
            params = (reservation_id, table)
            self.cursor.execute(add_table_command, params)

        self.database.commit()

    def get_res_from_id(self, res_id):
        command = """
        SELECT *
        FROM Reservation
        WHERE ResID = ?
        """
        params = (res_id,)
        self.cursor.execute(command, params)
        return self.cursor.fetchone()
    
    def update_res_status(self, reservation_id, new_status):
        command = """
        UPDATE Reservation
        SET ResStatus = ?
        WHERE ResID = ?
        """
        params = (new_status, reservation_id)
        self.cursor.execute(command, params)
        self.database.commit()

    # I wanna replace this with an SQL trigger
    def unreserve_table(self, reservation_id):
        command = """
        UPDATE Seating
        SET CurrentReservation = NULL
        WHERE TableID = (SELECT TableID FROM Reservation WHERE ResID = ?);
        """
        params = (reservation_id,)
        self.cursor.execute(command, params)
        self.database.commit()

    def calculate_wait_time(self):
        query = """
        SELECT 
            COUNT(*) AS total_rows, 
            SUM(CASE WHEN CurrentReservation IS NOT NULL THEN CurrentReservation + 60 ELSE 0 END) AS total_sum
        FROM Seating;
        """
        self.cursor.execute(query)
        total_rows, total_sum = self.cursor.fetchone()
        
        # Average calculation, treating NULLs as 0
        average = total_sum / total_rows if total_rows > 0 else 0
        return round(average, 0)

    ###
    #endregion RESERVATIONS
    ###

    ###
    #region RECURRING
    ###

    def remind_reservations(self) -> None: # pw: csc team 2
        command = """
        SELECT a.AccountEmail, a.AccountFN, r.ResTime
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

    def handle_no_shows(self) -> None:
        command = """
        SELECT a.AccountEmail, r.ResID FROM Account a, Reservation r             
        WHERE a.AccountID = r.ResID
        AND r.ResStatus = "ready"
        AND r.ResDate < ?
        OR (r.ResDate = ? AND r.ResTime < ?)
        """
        today = datetime.today().strftime('%Y-%m-%d')
        noshow_threshold = (datetime.now() - timedelta(minutes=30)).strftime('%H:%M:%S')
        params = (today, today, noshow_threshold)
        self.cursor.execute(command, params)
        
        for email, id in self.cursor.fetchall():
            self.send_email(email, 'Reservation No-Show', 'Hello!\nYou recently missed a reservation, and it has been noted.')
            self.update_res_status(id, "no_show")
            self.unreserve_table(id)
            print(f'Table with ID #{id} has been un-reserved.')

        # Keep this at the very end of this function
        self.database.commit()
    ###
    #endregion RECURRING
    ###

    ###
    #region INVENTORY
    ###
    # This is kinda a guess until we get a proper ordering page up
    # Still need to figure out how we are gunna do expiration date and stuff, maybe make a file for holding each item data?
    def order_meat(self, item, size, quantity: str, expiration_date: str) -> None:
        query = """
        INSERT INTO Inventory (Item, Size, Quantity, Expiration_Date)
        VALUES (?, ?, ?, ?)
        """
        if self.checkInventory(item, size, expiration_date):
            query = """
            UPDATE INVENTORY SET
            QUANTITY = ?
            WHERE
            ITEM = ?
            AND SIZE = ?
            AND EXPIRATION_DATE = ?
            """
            quantity += self.getQuantity(item, size, expiration_date)
            self.cursor.execute(query, (quantity, item, size, expiration_date))
        else:
            self.cursor.execute(query, (item, size, quantity, expiration_date))
        self.database.commit()
    
    def checkInventory(self, item, size, expiration_date) -> bool:
        query = """
        SELECT *
        FROM INVENTORY
        WHERE
        ITEM = ?
        AND SIZE = ?
        AND EXPIRATION_DATE = ?
        """
        self.cursor.execute(query, (item, size, expiration_date))
        if self.cursor.fetchall():
            return True
        return False

    def getQuantity(self, item, size, expiration_date) -> int:
        query = """
        SELECT Quantity
        FROM Inventory
        WHERE
        ITEM = ?
        AND SIZE = ?
        AND EXPIRATION_DATE = ?
        """
        self.cursor.execute(query, (item, size, expiration_date))
        quantity = self.cursor.fetchall()[0][0]
        return quantity
    ###
    #endregion INVENTORY
    ###

    ###
    #region MISC
    ###
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
            print(f"Email sent with subject: '{subject}'")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            server.quit()
    ###
    #endregion MISC
    ###

    ###
    #region OLD CODE
    ###
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
    ###
    #endregion OLD CODE
    ###