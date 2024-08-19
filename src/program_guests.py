import datetime
from dateutil import parser

from infrastructure.switchlang import switch
import program_hosts as hosts
import services.data_service as svc
import infrastructure.state as state


def run():
    print(' ****************** Welcome guest **************** ')
    print()

    show_commands()

    while True:
        action = hosts.get_action()

        with switch(action) as s:
            s.case('c', hosts.create_account)
            s.case('l', hosts.log_into_account)

            s.case('a', add_a_dog)
            s.case('y', view_your_dogs)
            s.case('b', book_a_kennel)
            s.case('v', view_bookings)
            s.case('m', lambda: 'change_mode')

            s.case('?', show_commands)
            s.case('', lambda: None)
            s.case(['x', 'bye', 'exit', 'exit()'], hosts.exit_app)

            s.default(hosts.unknown_command)

        state.reload_account()

        if action:
            print()

        if s.result == 'change_mode':
            return


def show_commands():
    print('Menu:')
    print('[C]reate an account')
    print('[L]ogin to your account')
    print('[B]ook a kennel')
    print('[A]dd a dog')
    print('View [y]our dogs')
    print('[V]iew your bookings')
    print('[M]ain menu')
    print('e[X]it app')
    print('[?] Help (this info)')
    print()


def add_a_dog():
    print(' ****************** Add a dog **************** ')
    if not state.active_account:
        hosts.error_msg("You must log in first to add a dog")
        return

    name = input("What is your dog's name? ")
    if not name:
        hosts.error_msg('cancelled')
        return

    size = input('How big is your dog? 0-small 1-medium 2-large ')
    breed = input("Breed? ")
    is_unsocial = input("Is your dog unsocial [y]es, [n]o? ").lower().startswith('y')

    dog = svc.add_dog(state.active_account, name, size, breed, is_unsocial)
    state.reload_account()
    hosts.success_msg('Created {} with id {}'.format(dog.name, dog.id))


def view_your_dogs():
    print(' ****************** Your dogs **************** ')
    if not state.active_account:
        hosts.error_msg("You must log in first to view your dogs")
        return

    dogs = svc.get_dogs_for_user(state.active_account.id)
    print("You have {} dogs.".format(len(dogs)))
    size_names = {0: "small", 1: "medium", 2: "large"}
    for s in dogs:
        size_name = size_names.get(s.size, "Unknown")
        print(" * {} is a {} that is {} sized and is {}unsocial.".format(
            s.name,
            s.breed,
            size_name,
            '' if s.is_unsocial else 'not '
        ))


def book_a_kennel():
    print(' ****************** Book a kennel **************** ')
    if not state.active_account:
        hosts.error_msg("You must log in first to book a kennel")
        return

    dogs = svc.get_dogs_for_user(state.active_account.id)
    if not dogs:
        hosts.error_msg('You must first [a]dd a dog before you can book a kennel.')
        return

    print("Let's start by finding available kennels.")
    start_text = input("Check-in date [yyyy-mm-dd]: ")
    if not start_text:
        hosts.error_msg('cancelled')
        return

    checkin = parser.parse(
        start_text
    )
    checkout = parser.parse(
        input("Check-out date [yyyy-mm-dd]: ")
    )
    if checkin >= checkout:
        hosts.error_msg('Check in must be before check out')
        return

    print()
    size_names = {0: "small", 1: "medium", 2: "large"}
    for idx, s in enumerate(dogs):
        size_name = size_names.get(s.size, "Unknown")
        print('{}. {} (size: {}, unsocial: {})'.format(
            idx + 1,
            s.name,
            size_name,
            'yes' if s.is_unsocial else 'no'
        ))

    dog = dogs[int(input('Which dog do you want to book a kennel for ?(number)')) - 1]

    kennels = svc.get_available_kennels(checkin, checkout, dog)

    print("There are {} kennels available in that time.".format(len(kennels)))
    for idx, c in enumerate(kennels):
        size_name = size_names.get(c.size, "Unknown")
        print(" {}. {} with is {} sized , has toys: {}.".format(
            idx + 1,
            c.name,
            size_name,

            'yes' if c.has_toys else 'no'))

    if not kennels:
        hosts.error_msg("Sorry, no kennels are available for that date.")
        return

    kennel = kennels[int(input('Which kennel do you want to book (number)')) - 1]
    svc.book_kennel(state.active_account, dog, kennel, checkin, checkout)

    hosts.success_msg('Successfully booked {} for {} at ${}/night.'.format(kennel.name, dog.name, kennel.price))


def view_bookings():
    print(' ****************** Your bookings **************** ')
    if not state.active_account:
        hosts.error_msg("You must log in first to register a kennel")
        return

    dogs = {s.id: s for s in svc.get_dogs_for_user(state.active_account.id)}
    bookings = svc.get_bookings_for_user(state.active_account.email)

    print("You have {} bookings.".format(len(bookings)))
    for b in bookings:
        # noinspection PyUnresolvedReferences
        print(' * Dog: {} is booked at {} from {} for {} days.'.format(
            dogs.get(b.guest_dog_id).name,
            b.kennel.name,
            datetime.date(b.check_in_date.year, b.check_in_date.month, b.check_in_date.day),
            (b.check_out_date - b.check_in_date).days
        ))
