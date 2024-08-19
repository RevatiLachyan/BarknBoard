import traceback
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, redirect, url_for, flash
from dateutil import parser
import services.data_service as svc
import infrastructure.state as state
import os
from data.mongo_setup import global_init
from dotenv import load_dotenv
load_dotenv()


global_init()
app = Flask(__name__)

print('test point 1')
print(f"FLASK_ENV: {os.getenv('FLASK_ENV')}")
logging.basicConfig(filename='error.log', level=logging.ERROR)
file_handler = RotatingFileHandler('complex.log', maxBytes=1024 * 1024 * 10, backupCount=5)
file_handler.setLevel(logging.INFO)  # Ensure level is set to INFO or lower
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
app.logger.addHandler(file_handler)

print('test point 4')

@app.route('/')
def home():
    app.logger.info("Home route accessed")
    return render_template('index.html')


@app.route('/guest', methods=['GET', 'POST'])
def guest():
    if request.method == 'POST':
        action = request.form['action']
        if action == 'create_account':
            return redirect(url_for('create_account_route'))
        elif action == 'login':
            return redirect(url_for('login'))
        elif action == 'add_dog':
            return redirect(url_for('add_dog_route'))
        elif action == 'book_kennel':
            return redirect(url_for('book_kennel_route'))
        elif action == 'view_dogs':
            return redirect(url_for('view_dogs_route'))
        elif action == 'view_bookings':
            return redirect(url_for('view_bookings_route'))
    return render_template('guest.html')


@app.route('/create_account_route', methods=['GET', 'POST'])
def create_account_route():
    if request.method == 'POST':
        email = request.form['email']
        svc.create_account(email)
        return render_template('guest.html')
    return render_template('create_account.html')

@app.route('/guest_home')
def guest_home():
    print("Logged in as")
    print(state.active_account.name)
    name = state.active_account.name
    return render_template('guest.html,name=name)

@app.route('/host_home')
def host_home():
    return render_template('host.html')




@app.route('/login', methods=['GET', 'POST'])
def login():
    app.logger.info("Login route accessed")
    print('test point 3')
    logging.basicConfig(filename='error.log', level=logging.ERROR)
    file_handler = RotatingFileHandler('complex.log', maxBytes=1024 * 1024 * 10, backupCount=5)
    file_handler.setLevel(logging.INFO)  # Ensure level is set to INFO or lower
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    app.logger.addHandler(file_handler)
    print("test point 2")
    try:
        if request.method == 'POST':
            email = request.form['email']
            role = request.form['role']
            state.active_account = svc.find_account_by_email(email)
            print(email)
            print(role)

            # Redirect based on role
            if role == 'guest':
                app.logger.info(f"Logged in as guest: {state.active_account.id}")
                return redirect(url_for('guest_home'))
            elif role == 'host':
                app.logger.info(f"Logged in as host: {state.active_account.id}")
                return redirect(url_for('host_home'))
            else:
                flash("Invalid role selected. Please choose either 'guest' or 'host'.")
                return redirect(url_for('home'))

        return render_template('index.html')
    except Exception as e:
        app.logger.error("Error in login_route: %s", traceback.format_exc())
        flash("An internal error occurred. Please try again later.")
        return redirect(url_for('home'))


@app.route('/add_dog', methods=['GET', 'POST'])
def add_dog_route():
    if request.method == 'POST':
        name = request.form['name']
        size = int(request.form['size'])
        breed = request.form['breed']
        is_unsocial = 'is_unsocial' in request.form
        svc.add_dog(state.active_account, name, size, breed, is_unsocial)
        return render_template('guest.html')
    return render_template('add_dog.html')


@app.route('/book_kennel', methods=['GET', 'POST'])
def book_kennel_route():
    dogs = svc.get_dogs_for_user(state.active_account.id)
    if request.method == 'POST':
        dog_id = int(request.form['dog_id'])
        checkin = parser.parse(request.form['checkin'])
        checkout = parser.parse(request.form['checkout'])
        svc.book_kennel(state.active_account, dog_id, checkin, checkout)
        render_template('guest.html')
    return render_template('book_kennel.html', dogs=dogs)


@app.route('/view_dogs')
def view_dogs_route():
    print(state.active_account.id)
    print(state.active_account)
    print(state)
    dogs = svc.get_dogs_for_user(state.active_account.id)
    return render_template('view_dogs.html', dogs=dogs)


@app.route('/view_bookings')
def view_bookings_route():
    bookings = svc.get_bookings_for_user(state.active_account.email)
    return render_template('view_bookings.html', bookings=bookings)


if __name__ == '__main__':
    app.secret_key = os.getenv('SECRET_KEY', 'your_default_secret_key')
    app.run(debug=os.getenv("DEBUG"))
