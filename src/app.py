import datetime
import traceback
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, redirect, url_for, flash
import services.data_service as svc
import infrastructure.state as state
import os

from data.bookings import Booking
from data.dogs import Dog
from data.kennels import Kennel
from data.mongo_setup import global_init
from dotenv import load_dotenv

load_dotenv()

global_init()
app = Flask(__name__)
app.secret_key = 'your_secret_key'

print('test point 1')
print(f"FLASK_ENV: {os.getenv('FLASK_ENV')}")
logging.basicConfig(filename='error.log', level=logging.ERROR)
file_handler = RotatingFileHandler('complex.log', maxBytes=1024 * 1024 * 10, backupCount=5)
file_handler.setLevel(logging.INFO)  # Ensure level is set to INFO or lower
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
app.logger.addHandler(file_handler)
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client['your_db_name']
print(db.list_collection_names())  # Should list 'bookings'


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
        name = request.form['name']
        email = request.form['email']
        new_owner = svc.create_account(name, email)
        state.active_account = new_owner
        return redirect(url_for('guest_home'))
    return render_template('create_account.html')


@app.route('/view_dogs')
def view_dogs_route():
    print(state.active_account.id)
    print(state.active_account)
    print(state)
    dogs = svc.get_dogs_for_user(state.active_account.id)
    return render_template('view_dogs.html', dogs=dogs)


@app.route('/check_kennels', methods=['GET'])
def check_kennels_route():
    # Fetch all kennels registered by the active account
    kennels = svc.find_kennels_for_user(state.active_account.id)

    # For each kennel, check if it's occupied
    for kennel in kennels:
        kennel.is_occupied = svc.is_kennel_occupied(kennel.id)

    return render_template('check_kennels.html', kennels=kennels)


@app.route('/guest_home')
def guest_home():
    print("Logged in as")
    print(state.active_account.name)
    name = state.active_account.name
    return render_template('guest.html', name=name)


@app.route('/admin_home')
def admin_home():
    print("Logged in as admin")
    return render_template('admin.html')


@app.route('/host_home')
def host_home():
    name = state.active_account.name
    return render_template('host.html', name=name)


@app.route('/login', methods=['GET', 'POST'])
def login():
    app.logger.info("Login route accessed")

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
                print("test point 11")
                print(state.active_account)
                app.logger.info(f"Logged in as guest: {state.active_account.id}")
                return redirect(url_for('guest_home'))
            elif role == 'host':
                app.logger.info(f"Logged in as host: {state.active_account.id}")
                return redirect(url_for('host_home'))
            elif svc.is_admin(email) and role == 'admin':
                app.logger.info(f"Logged in as admin")
                return redirect(url_for('admin_home'))
            else:
                flash("Invalid role selected. Please choose either 'guest' or 'host' or 'admin'.")
                return redirect(url_for('home'))

        return render_template('index.html')
    except Exception as e:
        app.logger.error("Error in login_route: %s", traceback.format_exc())
        flash("An internal error occurred. Please try again later.")
        return redirect(url_for('home'))


@app.route('/logout')
def logout():
    # Clear the active account
    if state.active_account is not None:
        flash("You have been logged out!", 'message')
    state.active_account = None

    # Redirect to the home or login page
    return redirect(url_for('home'))


@app.route('/book_kennel', methods=['GET', 'POST'])
def book_kennel_route():
    if request.method == 'POST':
        if 'find_kennels' in request.form:
            # User has clicked the "Find Available Kennels" button
            dog_id = request.form.get('dog_id')
            checkin_date = datetime.datetime.strptime(request.form.get('checkin'), '%Y-%m-%d')
            checkout_date = datetime.datetime.strptime(request.form.get('checkout'), '%Y-%m-%d')

            dog = Dog.objects(id=dog_id).first()
            available_kennels = svc.get_available_kennels(checkin_date, checkout_date, dog)
            print(available_kennels)
            if not available_kennels:
                error_message = "No kennels available for the selected dates."
                return render_template('book_kennel.html', error_message=error_message)

            return render_template('book_kennel.html', dogs=[dog], available_kennels=available_kennels,
                                   checkin_date=checkin_date, checkout_date=checkout_date)

        elif 'book_kennel' in request.form:
            print('test point 12')
            # User has selected a kennel and submitted the booking request
            dog_id = request.form.get('dog_id')
            kennel_id = request.form.get('kennel_id')
            checkin_date = datetime.datetime.strptime(request.form.get('checkin').split()[0], '%Y-%m-%d')
            checkout_date = datetime.datetime.strptime(request.form.get('checkout').split()[0], '%Y-%m-%d')

            dog = Dog.objects(id=dog_id).first()
            kennel = Kennel.objects(id=kennel_id).first()

            # Proceed to book the kennel
            svc.book_kennel(kennel, dog, checkin_date, checkout_date)
            flash("Kennel booked successfully!", 'success')
            return redirect(url_for('guest_home'))

    dogs = svc.get_dogs_for_user(state.active_account.id)
    return render_template('book_kennel.html', dogs=dogs, available_kennels=[], checkin_date=None, checkout_date=None)



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


@app.route('/add_kennel', methods=['GET', 'POST'])
def add_kennel_route():
    if request.method == 'POST':
        # Assuming active_account is available
        active_account = state.active_account

        name = request.form['name']
        allow_unsocial = bool(request.form.get('allow_unsocial'))
        has_toys = bool(request.form.get('has_toys'))
        size = int(request.form['size'])
        price = float(request.form['price'])

        try:
            svc.register_kennel(active_account, name, allow_unsocial, has_toys, size, price)
            flash("Kennel has been added!", 'success')
            return redirect(url_for('check_kennels_route', email=active_account.email))
        except Exception as e:
            return str(e), 400  # Return the error message and a 400 status code

    # If it's a GET request, render the form to add a kennel
    return render_template('add_kennel.html')


@app.route('/view_bookings')
def view_bookings_route():
    bookings = svc.get_bookings_for_user(state.active_account.email)
    return render_template('view_bookings.html', bookings=bookings)


@app.route('/view_bookings_host')
def view_bookings_host_route():
    print("About to call get_bookings_for_host")  # Debugging line
    bookings = svc.get_bookings_for_host(state.active_account.email)
    # bookings=bookings.sort(key=lambda b: b.check_in_date)
    print("After calling get_bookings_for_host")  # Debugging line
    return render_template('view_bookings_host.html', bookings=bookings)


@app.route('/add_available_date', methods=['GET', 'POST'])
def add_available_date_route():
    if request.method == 'POST':
        try:
            kennel_id = request.form['kennel_id']
            start_date = datetime.datetime.strptime(request.form['start_date'], '%Y-%m-%d')
            days = int(request.form['days'])

            kennel = Kennel.objects(id=kennel_id).first()
            if not kennel:
                flash("Kennel not found.")
                return redirect(url_for('add_available_date_route'))

            # Use the service function to add the available date
            kennel = svc.add_available_date(kennel, start_date, days)
            print(f"Kennel {kennel.name} is now available from {start_date} for 5 days.")
            flash("Available date added successfully!", 'success')
            return redirect(url_for('add_available_date_route'))
        except Exception as e:
            flash("An error occurred: " + str(e))
            return redirect(url_for('add_available_date_route'))

    # GET request: Show the form with a list of kennels
    kennels = Kennel.objects()  # Fetch all kennels
    return render_template('add_available_date.html', kennels=kennels)


@app.route('/analytics_dashboard', methods=['GET'])
@app.route('/analytics_dashboard/<plot_type>', methods=['GET'])
def analytics_dashboard(plot_type="booking_trends"):
    try:
        # Fetch booking and kennel data
        bookings = svc.get_all_bookings()
        kennels = svc.get_all_kennels()

        # Select plot data based on `plot_type`
        if plot_type == 'booking_trends':
            plot_data = svc.get_booking_trends(bookings)
        elif plot_type == 'kennel_occupancy':
            plot_data = svc.get_kennel_occupancy(kennels)
        elif plot_type == 'average_duration':
            plot_data = svc.get_average_booking_duration(bookings)
        elif plot_type == 'monthly_revenue':
            plot_data = svc.get_monthly_revenue(bookings)
        else:
            plot_data = None

        return render_template(
            'analytics_dashboard.html',
            plot_data=plot_data,
            plot_type=plot_type,
        )
    except Exception as e:
        app.logger.error("Error loading analytics dashboard: %s", traceback.format_exc())
        flash("An error occurred while loading the analytics dashboard.")
        return redirect(url_for('admin_home'))



if __name__ == '__main__':
    app.secret_key = os.getenv('SECRET_KEY', 'your_default_secret_key')
    app.run(debug=os.getenv("DEBUG"))
