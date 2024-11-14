import pyodbc

class Database:

    server = 'DESKTOP-MGE25SL'
    database = 'CSC450Inventory'

    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes'

    def __init__(self):
    
        self.conn = pyodbc.connect(self.conn_str)
        self.cursor = self.conn.cursor()
    
    def check_in_search(self, lastname):
        query = "SELECT * FROM Reservations WHERE Lastname = ?"
        self.cursor.execute(query, (lastname))
        results = self.cursor.fetchall()

        for row in results:
            print(row)
    
    def make_reservation(self, ResID, reservation_date, reservation_time, guests, TimeCreated, TimeUpdated, ResStatus, table_id, ResOwner):
        query = """
        INSERT INTO Reservation (ResID, ResDate, ResTime, ResNoGuests, TimeCreated, TimeUpdated, ResStatus, TableID, ResOwner)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.cursor.execute(query, (ResID, reservation_date, reservation_time, guests, TimeCreated, TimeUpdated, ResStatus, table_id, ResOwner))
        self.cursor.commit()
        
    def remind_reservations(self):
        return
    
    def close_connection(self):
        self.cursor.close()
        self.conn.close()
