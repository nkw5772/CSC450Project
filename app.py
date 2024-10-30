
from flask import Flask, render_template, redirect, url_for, request
from hashlib import sha256

app = Flask(__name__)

# Define the route for the login page
@app.route('/')
def index():
    return render_template('home.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route("/createAccount")
def createAccount():
    return render_template('createAccount.html')

@app.route('/submit-form', methods=['POST'])
def tryCreateAccount():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    phone_number = request.form.get('phone')
    password_hash = sha256(request.form.get('password').encode('utf-8')).hexdigest()
    password_confirm_hash = sha256(request.form.get('confirm_password').encode('utf-8')).hexdigest()

    if (password_hash != password_confirm_hash):
        # Fix this fr?
        print("PASSWORDS DO NOT MATCH")
        return render_template('home.html')
    
# # Define the route to handle login form submission
# @app.route('/login', methods=['POST'])
# def login():
#     username = request.form.get('username')
#     password = request.form.get('password')

#     # Check if credentials match
#     if username == 'matt' and password == 'salas':
#         return redirect(url_for('home'))
#     else:
#         return 'Incorrect username or password', 401

# # Define the route for the home page
# @app.route('/home')
# def home():
#     return '<h1>Welcome to the Home Page!</h1>'

if __name__ == '__main__':
    app.run(debug=True)