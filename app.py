
from flask import Flask, render_template, redirect, url_for, request, make_response
from hashlib import sha256

app = Flask(__name__)

# Define the route for the login page
@app.route('/')
def index():
<<<<<<< Updated upstream
    return render_template('home.html')
=======
    if request.method == 'POST':
        db = helper.Database()
        # Get the form data
        username = request.form.get('username')
        # password = request.form.get('password')
        password_hash = sha256(request.form.get('password').encode('utf-8')).hexdigest()
        
        # Check if the credentials are correct
        if db.verify_login(username, password_hash) == True: 
            resp = make_response(redirect(url_for('home')))
            resp.set_cookie('auth_token', username)
            return resp
            # return render_template('home.html')
        else:
            # Show an error message if credentials are incorrect
            # return redirect(url_for('error'))
            # return redirect(url_for('index'))
            error_message = "Invalid username or password. Please try again."
            return render_template('login.html', error_message=error_message)

    # If it's a GET request, render the login page
    return render_template('login.html')

@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('createAccount')))

    resp.delete_cookie('auth_token')

    return resp

@app.route("/home")
def home():
    username = request.cookies.get('auth_token')
    if username:
        return render_template('home.html')
    else:
        return "You are not logged in."
    
>>>>>>> Stashed changes

@app.route('/login')
def login():
    return render_template('login.html')

@app.route("/createAccount")
def createAccount():
<<<<<<< Updated upstream
=======
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
>>>>>>> Stashed changes
    return render_template('createAccount.html')

@app.route("/createReservation")
def createReservation():
    return render_template('createReservation.html')

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