
from flask import Flask, render_template, redirect, url_for, request
from hashlib import sha256
import database as helper
from datetime import datetime

app = Flask(__name__)

# Define the route for the login page
# This page is the root page of the application
# This will eventually query the database and check the credentials.
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        db = helper.Database()
        # Get the form data
        username = request.form.get('username')
        password = request.form.get('password')
        # password_hash = sha256(request.form.get('password').encode('utf-8')).hexdigest()
        
        # Check if the credentials are correct
        if db.verify_login(username, password) == True: 
            return redirect(url_for('home'))
            # return render_template('home.html')
        else:
            # Show an error message if credentials are incorrect
            # return redirect(url_for('error'))
            # return redirect(url_for('index'))
            error_message = "Invalid username or password. Please try again."
            return render_template('login.html', error_message=error_message)

    # If it's a GET request, render the login page
    return render_template('login.html')

@app.route("/home")
def home():
    return render_template('home.html')

@app.route("/createAccount", methods=['GET', 'POST'])
@app.route("/createAccount.html", methods=['GET', 'POST']) # Not sure about this
def createAccount():
    if request.method == 'POST':
        db = helper.Database()
        
        first_name = request.form.get('first_name') # Should we hash this info as well?
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone_number = request.form.get('phone')
        password_hash = sha256(request.form.get('password').encode('utf-8')).hexdigest()
        confirm_password_hash = sha256(request.form.get('confirm_password').encode('utf-8')).hexdigest()

        error_messages = []

        if not db.email_is_unique(email):
            error_messages.append('Email is already in use - please use a different email.')

        if not db.phone_is_unique(phone_number):
            error_messages.append('Phone number is already in use - please use a different phone number.')

        if password_hash != confirm_password_hash:
            error_messages.append('Passwords do not match.')
        
        if error_messages:
            return render_template('createAccount.html', error_messages=error_messages)
        else:
            today = datetime.today().strftime('%Y-%m-%d')
            db.add_account(first_name, last_name, 'Customer', email, phone_number, today, password_hash)
            return render_template('home.html', message=f"Welcome {first_name}!") # I wanna be able to redirect with parameters (haven't researched much yet)
            # return redirect(url_for('home'))

    # If it's a GET request, render the login page
    return render_template('createAccount.html')

"""
# Define the route to handle login form submission
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    # Check if credentials match
    if username == 'matt' and password == 'salas':
       return redirect(url_for('home'))
    else:
       return 'Incorrect username or password', 401
""" 


if __name__ == '__main__':
    app.run(debug=True)