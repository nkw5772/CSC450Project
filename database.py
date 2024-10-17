import pyodbc

connection = pyodbc.connect("Driver={SQL Server};\
                            Server=LAPTOP-FAI3GTFD;\
                            Database=Project;\
                            Trusted_Connection=yes;"
)

cursor = connection.cursor()
cursor.execute("Select * from Reservations")
for row in cursor.fetchall():
    print(row)