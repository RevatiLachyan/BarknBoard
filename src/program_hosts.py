import datetime
from colorama import Fore
from dateutil import parser

from infrastructure.switchlang import switch
import infrastructure.state as state
import services.data_service as svc


def run():
    print(' ****************** Welcome host **************** ')
    print()

    show_commands()

    while True:
        action = get_action()

        with switch(action) as s:
            s.case('c', create_account)
            s.case('a', create_account)
            s.case('l', log_into_account)
            s.case('y', list_kennels)
            s.case('r', register_kennel)
            s.case('u', update_availability)
            s.case('v', view_bookings)
            s.case('m', lambda: 'change_mode')
            s.case(['x', 'bye', 'exit', 'exit()'], exit_app)
            s.case('?', show_commands)
            s.case('', lambda: None)
            s.default(unknown_command)

        if action:
            print()

        if s.result == 'change_mode':
            return


def show_commands():
    print('What action would you like to take:')
    print('[C]reate an [a]ccount')
    print('[L]ogin to your account')
    print('List [y]our kennels')
    print('[R]egister a kennel')
    print('[U]pdate kennel availability')
    print('[V]iew your bookings')
    print('Change [M]ode (guest or host)')
    print('e[X]it app')
    print('[?] Help (this info)')
    print()


def create_account():
    print(' ****************** REGISTER **************** ')

    name = input('What is your name? ')
    email = input('What is your email? ').strip().lower()
    print(f"Email entered: {email}")
    old_account = svc.find_account_by_email(email)
    print(old_account)
    # print('test point 1')
    if old_account:
        print('test point 5')
        error_msg(f"ERROR: Account with email {email} already exists.")
        return
    # print('test point 2')

    state.active_account = svc.create_account(name, email)
    # print('test point 3')
    success_msg(f"Created new account with id {state.active_account.id}.")
    # print('test point 4')


def log_into_account():
    print(' ****************** LOGIN **************** ')

    email = input('What is your email? ').strip().lower()
    account = svc.find_account_by_email(email)

    if not account:
        error_msg(f'Could not find account with email {email}.')
        return

    state.active_account = account
    success_msg('Logged in successfully.')


def register_kennel():
    print(' ****************** REGISTER KENNEL **************** ')

    if not state.active_account:
        error_msg('You must login first to register a kennel.')
        return

    size = input('How big is the kennel? 0-small 1-medium 2-large ')
    if not size:
        error_msg('Cancelled')
        return


    #carpeted = input("Is it carpeted [y, n]? ").lower().startswith('y')
    has_toys = input("Have dog toys [y, n]? ").lower().startswith('y')
    allow_unsocial = input("Can you host unsocial dogs [y, n] (have a separate yard)? ").lower().startswith('y')
    name = input("Give your kennel a name: ")
    price = float(input("How much are you charging?  "))

    kennel = svc.register_kennel(
        state.active_account, name,
        allow_unsocial, has_toys, size, price
    )

    state.reload_account()
    success_msg(f'Register new kennel with id {kennel.id}.')


def list_kennels(suppress_header=False):
    if not suppress_header:
        print(' ******************     Your kennels     **************** ')

    if not state.active_account:
        error_msg('You must login first to register a kennel.')
        return
    size_names = {0: "small", 1: "medium", 2: "large"}
    kennels = svc.find_kennels_for_user(state.active_account)
    print(f"You have {len(kennels)} kennels.")
    for idx, c in enumerate(kennels):
        size_name = size_names.get(c.size, "Unknown")  # Get size name or "Unknown" if size is not found
        print(f'{idx + 1}. {c.name} is {size_name} sized.')
        for b in c.bookings:
            print('      * Booking: {}, {} days, booked? {}'.format(
                b.check_in_date,
                (b.check_out_date - b.check_in_date).days,
                'YES' if b.booked_date is not None else 'no'
            ))


def update_availability():
    print(' ****************** Add available date **************** ')

    if not state.active_account:
        error_msg("You must log in first to register a kennel")
        return

    list_kennels(suppress_header=True)

    kennel_number = input("Enter kennel number: ")
    if not kennel_number.strip():
        error_msg('Cancelled')
        print()
        return

    kennel_number = int(kennel_number)

    kennels = svc.find_kennels_for_user(state.active_account)
    selected_kennel = kennels[kennel_number - 1]

    success_msg("Selected kennel {}".format(selected_kennel.name))

    start_date = parser.parse(
        input("Enter available date [yyyy-mm-dd]: ")
    )
    days = int(input("How many days is this block of time? "))

    svc.add_available_date(
        selected_kennel,
        start_date,
        days
    )

    success_msg(f'Date added to kennel {selected_kennel.name}.')


def view_bookings():
    print(' ****************** Your bookings **************** ')

    if not state.active_account:
        error_msg("You must log in first to register a kennel")
        return

    kennels = svc.find_kennels_for_user(state.active_account)

    bookings = [
        (c, b)
        for c in kennels
        for b in c.bookings
        if b.booked_date is not None
    ]

    print("You have {} bookings.".format(len(bookings)))
    for c, b in bookings:
        print(' * Kennel: {}, booked date: {}, from {} for {} days.'.format(
            c.name,
            datetime.date(b.booked_date.year, b.booked_date.month, b.booked_date.day),
            datetime.date(b.check_in_date.year, b.check_in_date.month, b.check_in_date.day),
            b.duration_in_days
        ))


def exit_app():
    print()
    print('bye')
    raise KeyboardInterrupt()


def get_action():
    text = '> '
    if state.active_account:
        text = f'{state.active_account.name}> '

    action = input(Fore.YELLOW + text + Fore.WHITE)
    return action.strip().lower()


def unknown_command():
    print("Sorry we didn't understand that command.")


def success_msg(text):
    print(Fore.LIGHTGREEN_EX + text + Fore.WHITE)


def error_msg(text):
    print(Fore.LIGHTRED_EX + text + Fore.WHITE)
