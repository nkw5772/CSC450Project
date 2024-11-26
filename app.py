
from flask import Flask, render_template, redirect, flash, url_for, request, jsonify, session, make_response
from hashlib import sha256
from database import Database
from datetime import datetime, timedelta
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import time
import threading
import os

###
#region GLOBAL
###
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Secret key for session management
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict' # Blocks cross-site cookies

limiter = Limiter(
    get_remote_address,  # This will use the user's IP to track rate limits
    app=app,
    default_limits=["15 per second", ]  # Default limits for all routes
)

disable_login_limit = False # Toggles whether login attempt rate is limited (enable if needed for testing)
###
#endregion GLOBAL
###

###
#region USER AUTHENTICATION
###
# Define the route for the login page
# This page is the root page of the application
# This will eventually query the database and check the credentials.
@app.route('/', methods=['GET', 'POST'])
# @limiter.limit("5 per minute")
def login():
    if 'email' in session:
        return redirect(url_for('home'))
     # Track login attempts using sessions
    if 'login_attempts' not in session:
        session['login_attempts'] = []
    #ALL THIS^^^^^^^
        
    # Record the current timestamp for each attempt
    current_time = time.time()
    
    session['login_attempts'] = [t for t in session['login_attempts'] if current_time - t < 60]  # Keep only attempts within the last 60 seconds
    #THIS^
    

    # # Check if the user has exceeded the limit
    if len(session['login_attempts']) >= 5:
        return render_template('login.html', error_message="Too many login attempts. Please try again later")
    #THIS^
    #ACTUAL LOGIN LOGIC
    if request.method == 'POST':
        db = Database()

        email = request.form.get('email')
        password_hash = sha256(request.form.get('password').encode('utf-8')).hexdigest()
        
        # Check if the credentials are correct
        if db.verify_login(email, password_hash): 
            # Creates a cookie for user when they login
            session['email'] = email
            session['account_type'] = db.get_account_type(email)
            return redirect(url_for("home"))
        
            # Add the current attempt timestamp for invalid login
            # if not disable_login_limit:
            #     session['login_attempts'].append(current_time)
            
            # if len(session['login_attempts']) >= 5:
            #     return render_template('login.html', error_message="Too many login attempts. Please try again later")
            #THIS^
            
        else:
            # Show an error message if credentials are incorrect
            error_message = 'Invalid username or password. Please try again.'
            return render_template('login.html', error_message=error_message)


    # If it's a GET request, render the login page
    response = make_response(render_template('login.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private' # Prevent page caching so user can't use browser back button to reach page after logging in
    response.headers['Pragma'] = 'no-cache' # Same thing but for backwards compatibility with older browsers
    response.headers['Expires'] = '0' # Ditto
    return response

@app.route('/logout')
def logout():
    # Deletes user's cookies and returns them to login page
    session.clear()
    return redirect(url_for('login'))

@app.route("/createAccount", methods=['GET', 'POST'])
def createAccount():
    if request.method == 'POST':
        db = Database()
        
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
            db.add_account(first_name, last_name, 'customer', email, phone_number, today, password_hash)
            # return render_template('home.html', message=f"Welcome {first_name}!") # I wanna be able to redirect with parameters (haven't researched much yet)
            return redirect(url_for('home', login_sucess=True))

    # If it's a GET request, render the login page
    return render_template('createAccount.html')
###
#endregion USER AUTHENTICATION
###


@app.route("/home")
def home():
    if 'email' not in session:
        return redirect(url_for('login'))
    disable_script = """
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const loginButton = document.getElementById('login-btn');
            if (loginButton) {
                loginButton.style.backgroundColor = '#808080';
                loginButton.style.pointerEvents = 'none';
            }
        });
    </script>
    """
    db = Database()
    user_notifs = db.get_account_notifications(session.get('email'))
    if user_notifs:
        return render_template('home.html', user_notifs=user_notifs, remove_notification=db.remove_notification, disable_script=disable_script)
    return render_template('home.html', remove_notification=db.remove_notification, disable_script=disable_script)

###
#region INVENTORY
###
@app.route("/ordering", methods=['GET', 'POST'])
def ordering():
    # Need to make it so only employees can get here
    return render_template('ordering.html')

@app.route('/submitorder', methods=['POST'])
def submitorder():
    try:
    # Gets data from ordering form
        item = request.form.get('item')  # Corresponds to "Item" column
        size = request.form.get('size')  # Corresponds to "Size" column
        quantity = int(request.form.get('quantity'))  # Quantity as integer
        expiration_date = (datetime.now() + timedelta(weeks=2)).strftime('%Y-%m-%d')  # 2 weeks from now

        db = Database()

        db.order_meat(item, size, quantity, expiration_date)

        return jsonify({'message': 'Order submitted successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
###
#endregion INVENTORY
###

###
#region RESERVATIONS
###
@app.route("/reservation", methods=['GET', 'POST'])
def reservations():
    if 'email' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST': # When modifying a res through /myReservations
        res_id = request.form.get('reservation_id')
        return render_template('reservation.html', res_id = res_id)
    db = Database()
    wait_time = db.calculate_wait_time()
    print(f"wait time, debugging porpoises: {wait_time}")
    return render_template('reservation.html', wait_time=wait_time)

@app.route('/reserve', methods=['POST'])
def reserve_table():
    try:
        data = request.get_json(silent=True, cache=True)
        if not data:
            return redirect(url_for('/reservation'))
        
        # Extract form data from the request
        guests = data.get('guests')
        res_date = data.get('reservation_date')
        res_time = data.get('reservation_time')
        table_ids = data.get('table_ids')
        res_id = data.get('reservation_id', None)
    
        # guests = request.form.get('guests')
        # res_date = request.form.get('reservation_date')
        # res_time = request.form.get('reservation_time')
        # table_id = request.form.get('table_id')
        # res_id = request.form.get('reservation_id', default = None)

        # Establish connection to the SQL Server
        db = Database()
        for table in table_ids:
            if db.check_reservation_conflict(table, res_date, res_time):
                return jsonify({'error': 'This table is already reserved at the selected time. Please choose another time or table.'}), 409


        print(f"Guests: {guests}, Date: {res_date}, Time: {res_time}, Table IDs: {table_ids}")
        now = datetime.now().strftime('%H:%M:%S')
        if res_id:
            current_res = db.get_res_from_id(res_id)
            time_created = current_res[4]
            res_owner = current_res[8]
            db.modify_reservation(res_id, res_date, res_time, guests, time_created, now, 'scheduled', table_ids, res_owner)
        else:
            db.make_reservation(res_date, res_time, guests, now, now, "scheduled", table_ids, db.get_id_from_email(session['email']))                

        return jsonify({'message': 'Reservation successful!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/checkInReservation", methods=['GET', 'POST'])
def checkIn():
    print(session.get('account_type'))
    if 'email' not in session or session.get('account_type')!= 'employee':
        flash('Sorry, you do not have permission to view that page.')
        return redirect(url_for('home'))
    if request.method == 'POST':
        db = Database()
        last_name = request.form.get('last_name')
        resSearch = db.check_in_search(last_name)
        
        # Check if no results were found
        if not resSearch:
            error = 'No reservation with the provided name.'
            return render_template('checkInReservation.html', resSearch=None, error=error)
        
        return render_template('checkInReservation.html', resSearch=resSearch)

    return render_template('checkInReservation.html')

# Route to perform the actual check-in action by updating reservation status
@app.route("/confirmCheckIn", methods=['POST'])
def confirmCheckIn():
    db = Database()
    reservation_id = request.form.get('reservation_id')
    print('Attempting to check in reservation with ResID:', reservation_id)
    # Attempt to check in the reservation
    check_in_success = db.check_in_reservation(reservation_id)
    
    last_name = request.form.get('last_name')
    resSearch = db.check_in_search(last_name) if last_name else None

    if check_in_success:
        message = 'Successfully checked in reservation.'
        return render_template('checkInReservation.html', resSearch=resSearch, message=message)
    else:
        error = 'Failed to check in reservation.'
        return render_template('checkInReservation.html', resSearch=resSearch, error=error)

@app.route('/reservationInfo', methods=['GET', 'POST'])
def reservationInfo():
    return render_template('reservationInfo.html')

@app.route('/getSeatCount', methods=['POST'])
def getSeatCount():
    data = request.get_json()['tables']

    db = Database()

    db.get_table_seat_count()

@app.route('/myReservations', methods=['GET', 'POST'])
def my_reservations():
    db = Database()
    
    name = db.get_name_from_email(session['email'])[0]
    reservations = db.get_user_reservations(session['email'])

    if request.method == 'POST': # If cancelling a res 
        try:
            res_id = request.form.get('reservation_id')
            db.update_res_status(res_id, 'cancelled')
            db.unreserve_table(res_id)
            return render_template('myReservations.html', name = name, reservations = reservations, message = 'Reservation cancelled successfully!')
        except:
            return render_template('myReservations.html', name = name, reservations = reservations, error = 'Unable to cancel reservation. Oops lmao')

    return render_template('myReservations.html', name = name, reservations = reservations)
###
#endregion RESERVATIONS
###

"""
# Triggered before every request (GET/POST) and checks if session account type matches database and flags if not
@app.before_request
def load_user():
    email = session['email']
    if email:
        db = Database()
        try:
            session['account_type'] = db.get_account_type(email)
        except:
            return jsonify({"error": "Could not validate user account type. Please try again later."}), 418 # TODO: Find a better error code lmao
    else:
        session['account_type'] = 'customer'  # Default role if not logged in
"""

"""
def refresh_app():
    '''
    Refreshes the app every 60 seconds so that the application is display real time data. 
    '''
    while True:
        time.sleep(60)  # Wait for 60 seconds
        print("Refreshing Flask app...")
        os.system("touch app.py")  # Trigger a "file change" in app.py to force reload
"""

def check_stuff():
    try:
        threading.Timer(60, check_stuff).start()
    except RuntimeError:
        pass # Do nothing, just prevent a pointless error in console

    db = Database()
    db.remind_reservations()
    # db.handle_no_shows()

@app.errorhandler(429)
def ratelimit_error(e):
    return render_template('login.html', error_message='Too many login attempts. Please try again later.'), 429

if __name__ == '__main__':
    # check_stuff()
    # threading.Thread(target=refresh_app, daemon=True).start()
    app.run(debug=True) # Ok so setting debug=True gives a random Windows error that idk how to suppress, BUT it doesn't make the error when debug=False