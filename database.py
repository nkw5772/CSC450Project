import mysql.connector

mydb = mysql.connector.connect(
    host="PLACEHOLDER",
    user="PLACEHOLDER",
    password="PLACEHOLDER",
    database="PLACEHOLDER"
)

mycursor = mydb.cursor()