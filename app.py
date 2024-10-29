
from flask import Flask, render_template, redirect, url_for, request

app = Flask(__name__)

# Define the route for the login page
@app.route('/')
def index():
    return render_template('home.html')

@app.route('/login')
def login():
    return render_template('login.html')










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