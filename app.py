
from flask import Flask, render_template, redirect, url_for, request
from hashlib import sha256

app = Flask(__name__)

# Define the route for the login page
# This page is the root page of the application
# This will eventually query the database and check the credentials.
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get the form data
        username = request.form.get('username')
        password = request.form.get('password')
        print(username, password)
        # Check if the credentials are correct
        if username == 'matthew' and password == 'salas':
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
    confirm_password_hash = sha256(request.form.get('confirm_password').encode('utf-8')).hexdigest()

    # if email is not unique:
        # FAIL


    # if phone_number is not unique:
        # FAIL
    # @@ -32,14 +36,11 @@ 
    if password_hash != confirm_password_hash:
        # Fix this fr?
        print("PASSWORDS DO NOT MATCH")
        return render_template('home.html')
    
    # if all the checks pass, then create a database entry for new user
    pass
    


    # if email is not unique:
        # FAIL
    
    # if phone_number is not unique:
        # FAIL






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