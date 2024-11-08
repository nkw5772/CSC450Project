# CSC450Project

A restaurant reservation and inventory management system

## Libraries

### Install Required Libraries

Run `pip install -r requirements.txt` in the root directory

### mysql-connector-python

Used to connect to, query, and modify a MySQL database

### Flask Limiter

Used to set connection & query limits (prevents DDoS and stuff)

### Flask App

Framework for hosting webpages dynamically generated using Python

**Run Flask** (Debug Mode) - `python app.py` OR click the "Run Python File" button while viewing [app.py](app.py). This will run the Flask app and have it be able to change in real-time when code is edited.

> To run without debug mode enabled, run `flask run` in the root directory OR remove `debug=True` from the last line of [app.py](app.py)
