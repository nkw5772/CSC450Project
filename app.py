
from flask import Flask, render_template, redirect, flash, url_for, request, jsonify, session, make_response, Response
from hashlib import sha256
from database import Database
from datetime import datetime, timedelta
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from validate_email import validate_email
import time
import threading
import os
import re
import json

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
# TODO: Server-side checks for this
@app.route('/', methods=['GET', 'POST'])
def login():
    session.pop('reservation_chosen', None)
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

        # If either are null somehow, don't go any further
        missing = None
        if not email:
            missing = 'email'
        elif not password_hash:
            missing = 'password'
        if missing:
            error_message = f'Please provide a {missing}.'
            return render_template('login.html', error_message)
        
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

def validate_input(input, correct_type: type, min_length: int = 0, max_length: int = 0):
    if not input: # Check for null
        return False
    elif not isinstance(input, correct_type): # Check for right data type
        return False
    # Check for length constraints
    elif min_length > 0 and len(input) < min_length:
        return False
    elif max_length > 0 and len(input) > max_length:
        return False
    return True

@app.route("/createAccount", methods=['GET', 'POST'])
def createAccount():
    if request.method == 'POST':
        db = Database()

        error_messages = []

        # Get submitted info
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone_number = request.form.get('phone')
        password = request.form.get('password') 
        confirm_password = request.form.get('confirm_password') 

        # Validate info
        if not validate_input(first_name, str, 2, 50):
            error_messages.append('First name must be between 2 and 50 characters.')
        
        if not validate_input(last_name, str, 2, 50):
            error_messages.append('Last name must be between 2 and 50 characters.')

        if not (validate_input(email, str, 3, 100) and validate_email(email)):
            error_messages.append('Email could not be validated - please use a different email.')
        elif not db.email_is_unique(email):
            error_messages.append('Email is already in use - please use a different email.')

        if not (validate_input(phone_number, str, 10, 18) and re.fullmatch(r"^(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$", phone_number)): # Phone number regex: https://stackoverflow.com/a/16699507
            error_messages.append('Phone number could not be validated - please use a different phone number.')
        elif not db.phone_is_unique(phone_number):
            error_messages.append('Phone number is already in use - please use a different phone number.')
        
        if not (validate_input(password, str, 8) and validate_input(confirm_password, str, 8)):
            error_messages.append('Passwords must be at least 8 characters.')
        else:
            password_hash = sha256(password.encode('utf-8')).hexdigest()
            confirm_password_hash = sha256(confirm_password.encode('utf-8')).hexdigest()
            if password_hash != confirm_password_hash:
                error_messages.append('Passwords do not match.')
        
        # Return success or error
        if error_messages:
            return render_template('createAccount.html', error_messages=error_messages), 400
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
    session.pop('reservation_chosen', None)
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
    session.pop('reservation_chosen', None)
    if session.get('account_type') != 'manager':
        return redirect(url_for('home'))
    return render_template('ordering.html')

# TODO: Server-side checks for this
@app.route('/submitorder', methods=['POST'])
def submitorder():
    try:
    # Gets data from ordering form
        foodType = request.form.get('item')
        quantity = request.form.get('quantity')
        size = request.form.get('size')
        currentTime = datetime.now()
        purchaseDate = currentTime.strftime("%Y-%m-%d")
        purchaseTime = currentTime.strftime("%H:%M:%S")
        futureTime = datetime.now() + timedelta(weeks=2)
        expirationDate = futureTime.strftime("%Y-%m-%d")
        expirationTime = futureTime.strftime("%H:%M:%S")
        inventoryStatus = "ordered"

        db = Database()
        db.order_meat(foodType, quantity, size, purchaseDate, purchaseTime, expirationDate, expirationTime, inventoryStatus)

        return render_template('ordering.html')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# TODO: Server-side checks for this
@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    session.pop('reservation_chosen', None)

    db = Database()
    inventory = db.getInventory()

    if request.method == 'POST':  # If removing an item
        inventoryID = request.form.get('inventory_id')
        db.removeItem(inventoryID)
        inventory = db.getInventory()

        # Trigger low stock check
        account_id = db.get_id_from_email(session['email'])
        db.check_low_stock_and_notify(account_id)

    # Notify about expired items
    if session.get('account_type') in ['employee', 'manager']:
        account_id = db.get_id_from_email(session.get('email'))
        db.notify_expired_items(account_id)

    return render_template('inventory.html', inventory=inventory)


###
#endregion INVENTORY
###

###
#region NOTIFICATIONS
###
@app.route('/remove_notification', methods=['POST'])
def remove_notification():
    notification_id = request.form.get('notification_id')

    if notification_id:
        db = Database()
        db.remove_notification(notification_id)

    # Redirect back to the home page to show updated notifications
    return redirect(url_for('home'))

@app.route('/check_low_stock', methods=['POST'])
def check_low_stock():
    if session.get('account_type') != 'employee':
        return jsonify({'error': 'Unauthorized access'}), 403

    db = Database()
    account_id = db.get_id_from_email(session['email'])
    db.check_low_stock_and_notify(account_id)
    
    return jsonify({'message': 'Low stock notifications updated'}), 200

###
#endregion NOTIFICATIONS
###

###
#region RESERVATIONS
###
def no_cache(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# TODO: Server-side checks for this
@app.route("/reservation", methods=['GET', 'POST'])
def reservations():
    if 'reservation_chosen' not in session:
        flash('You must select reservation info first.')
        return redirect(url_for('reservationInfo'))
    reserved_tables_json = request.args.get('reserved_tables')
    seat_count = request.args.get('seat_count')
    reservation_date = request.args.get('reservation_date')
    reservation_time = request.args.get('reservation_time')
    print(reservation_time)
    reservation_time_plus_60 = request.args.get('reservation_time_plus_60')
    if reserved_tables_json:
        # Convert the JSON string back to a Python list
        reserved_tables = json.loads(reserved_tables_json)
    else:
        reserved_tables = []
    if request.method == 'POST': # When modifying a res through /myReservations
        res_id = request.form.get('reservation_id')
        return render_template('reservation.html', res_id = res_id)
    db = Database()
    wait_time = db.calculate_wait_time()
    # print(f"wait time, debugging porpoises: {wait_time}")
    return render_template('reservation.html', wait_time=wait_time, reserved_tables=reserved_tables, seat_count=seat_count, reservation_date=reservation_date, reservation_time=reservation_time, reservation_time_plus_60=reservation_time_plus_60)

# TODO: Server-side checks for this
@app.route('/reserve', methods=['POST'])
def reserve_table():
    try:
        data = request.get_json(silent=True)
        if not data:
            return redirect(url_for('/reservation'))
        
        # Extract form data from the request
        guests = data.get('guests')
        res_date = data.get('reservation_date')
        res_time = data.get('reservation_time')
        table_ids = data.get('table_ids')
        res_id = data.get('reservation_id', None)

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

# TODO: Server-side checks for this
@app.route("/checkInReservation", methods=['GET', 'POST'])
def checkIn():
    if session.get('account_type') not in ['employee', 'manager']:
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

# TODO: Server-side checks for this
@app.route('/reservationInfo', methods=['GET', 'POST'])
def reservationInfo():
    session.pop('reservation_chosen', None)
    
    if request.method == 'POST':
        
        seat_count = request.form.get('seat_count')
        reservation_date = request.form.get('reservation_date')
        reservation_time = request.form.get('reservation_time')
        
        # db = Database()
        # something = db.filter_reservations(reservation_time, reservation_date)
        # print(something)
        # minutes = reservation_time[3:5]
        # if minutes != "00" and minutes != "30":
        #     some_error = "Reservation time must end in :00 or :30"
        #     return render_template('reservationInfo.html', some_error=some_error)
        table_numbers = []
        db = Database()
        reserved_tables = db.filter_reservations(reservation_date)
        for i in reserved_tables:
            res_time_obj = datetime.strptime(i[1], "%H:%M")
        
            # Add 60 minutes to the reservation_time
            res_time_plus_60_obj = res_time_obj + timedelta(minutes=60)
            reservation_time_plus_60 = res_time_plus_60_obj.strftime("%H:%M")
            if reservation_time >= i[1] and reservation_time < reservation_time_plus_60:
                table_numbers.append(i[0])
        
        reserved_tables_json = json.dumps(table_numbers)
        
        session['reservation_chosen'] = 'reservation_status'
        return redirect(url_for('reservations',reserved_tables=reserved_tables_json, seat_count=seat_count, reservation_date=reservation_date, reservation_time=reservation_time))
    
    return render_template('reservationInfo.html')

# I looked up the route for this across all project files and this isn't referenced anywhere
"""
@app.route('/getSeatCount', methods=['POST'])
def get_seat_count():
    tables = request.get_json()

    db = Database()

    return jsonify(db.get_table_seat_count(tables))
"""

# TODO: Server-side checks for this
@app.route('/myReservations', methods=['GET', 'POST'])
def my_reservations():
    session.pop('reservation_chosen', None)

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

# Triggered before every request (GET/POST) and checks if session account type matches database and flags if not
@app.before_request
def verify_user():
    if 'email' not in session and request.path != '/':
        return redirect(url_for('login'))

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
    db.handle_no_shows()

@app.errorhandler(429)
def ratelimit_error(e):
    return render_template('login.html', error_message='Too many login attempts. Please try again later.'), 429

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') is None: # Flask debug mode makes check_stuff() run twice and this prevents that
        check_stuff()
    # threading.Thread(target=refresh_app, daemon=True).start()
    app.run(debug=True) # Ok so setting debug=True gives a random Windows error that idk how to suppress, BUT it doesn't make the error when debug=False