from typing import List, Optional
import datetime
from colorama import Fore
import bson
from data.bookings import Booking
from data.kennels import Kennel
from data.owners import Owner
from data.dogs import Dog
import logging


def create_account(name: str, email: str) -> Owner:
    owner = Owner()
    owner.name = name
    owner.email = email

    owner.save()

    return owner


def find_account_by_email(email: str) -> Owner:
    try:
        owner = Owner.objects(email=email).first()
        return owner
    except Exception as e:
        logging.info(f"Error retrieving account with email {email}: {e}")
        return None


def register_kennel(active_account: Owner,
                    name, allow_unsocial, has_toys
                    , size, price) -> Kennel:
    # Ensure size is an integer
    size = int(size)
    if size not in [0, 1, 2]:
        raise ValueError(f"Invalid size value: {size}. Must be one of [0, 1, 2].")
    kennel = Kennel()

    kennel.name = name
    kennel.size = size
    kennel.has_toys = has_toys
    kennel.allow_unsocial_dogs = allow_unsocial
    kennel.price = price

    kennel.save()

    account = find_account_by_email(active_account.email)
    account.kennel_ids.append(kennel.id)
    account.save()

    return kennel


import datetime
from data.kennels import Kennel
from data.bookings import Booking

def add_available_date(kennel: Kennel, start_date: datetime.datetime, days: int) -> Kennel:
    # Create a new Booking instance for the availability period
    booking = Booking(
        check_in_date=start_date,
        check_out_date=start_date + datetime.timedelta(days=days)
    )

    # Find the kennel in the database and add the new booking as an available slot
    kennel = Kennel.objects(id=kennel.id).first()
    if kennel is None:
        raise ValueError("Kennel not found")

    # Add the booking to the kennel's booking list
    kennel.bookings.append(booking)
    kennel.save()

    return kennel


def is_kennel_available(kennel: Kennel, checkin: datetime.datetime, checkout: datetime.datetime) -> bool:
    for window in kennel.available_dates:
        if window['start_date'] <= checkin and window['end_date'] >= checkout:
            return True
    return False


def add_dog(account, name, size, breed, is_unsocial) -> Dog:
    dog = Dog()
    dog.name = name
    dog.size = size
    dog.breed = breed
    dog.is_unsocial = is_unsocial
    dog.save()

    owner = find_account_by_email(account.email)
    owner.dog_ids.append(dog.id)
    owner.save()

    return dog


def add_kennel(account, name, price, size, has_toys,allow_unsocial_dogs) -> Kennel:
    kennel = Kennel()
    kennel.name = name
    kennel.size = size
    kennel.price = price
    kennel.has_toys = has_toys
    kennel.allow_unsocial_dogs=allow_unsocial_dogs
    kennel.save()

    owner = find_account_by_email(account.email)
    owner.kennel_ids.append(kennel.id)
    owner.save()

    return kennel

def find_kennels_for_user(user_id: bson.ObjectId) -> List[Kennel]:
    owner = Owner.objects(id=user_id).first()
    kennels = Kennel.objects(id__in=owner.kennel_ids).all()

    return list(kennels)

def get_dogs_for_user(user_id: bson.ObjectId) -> List[Dog]:
    owner = Owner.objects(id=user_id).first()
    dogs = Dog.objects(id__in=owner.dog_ids).all()

    return list(dogs)


def get_available_kennels(checkin: datetime.datetime,
                          checkout: datetime.datetime, dog: Dog) -> List[Kennel]:
    print('test point 10')
    # Ensure the kennel size is suitable for the dog
    query = Kennel.objects() \
        .filter(size__gte=dog.size) \

    if dog.is_unsocial:
        query = query.filter(allow_unsocial_dogs=True)

    # Order by price and size to prioritize more affordable kennels
    kennels = query.order_by('price', '-size')

    final_kennels = []
    for c in kennels:
        is_available = True
        for b in c.bookings:
            # Check for overlap with existing bookings
            if not (checkout <= b.check_in_date or checkin >= b.check_out_date):
                if b.guest_dog_id is not None:
                    is_available = False
                    break

        # If the kennel is available for the entire requested period, add it to the list
        if is_available:
            final_kennels.append(c)

    return final_kennels


def book_kennel(kennel: Kennel, dog: Dog, checkin: datetime.datetime, checkout: datetime.datetime):

    # Create a new booking for the dog
    new_booking = Booking(
        guest_dog_id=dog.id,
        check_in_date=checkin,
        check_out_date=checkout
    )

    # Handle existing bookings: remove any conflicting bookings and adjust the schedule
    updated_bookings = []
    for booking in kennel.bookings:
        if booking.check_in_date < checkout and booking.check_out_date > checkin:
            if booking.check_in_date < checkin:
                # Existing booking starts before the new booking
                split_before = Booking(
                    guest_dog_id=None,
                    check_in_date=booking.check_in_date,
                    check_out_date=checkin-datetime.timedelta(days=1)
                )
                updated_bookings.append(split_before)

            if booking.check_out_date > checkout:
                # Existing booking ends after the new booking
                split_after = Booking(
                    guest_dog_id=None,
                    check_in_date=checkout+datetime.timedelta(days=1),
                    check_out_date=booking.check_out_date
                )
                updated_bookings.append(split_after)

            # Skip the existing booking as it overlaps with the new booking
        else:
            updated_bookings.append(booking)

    # Add the new booking for the dog
    updated_bookings.append(new_booking)
    print(updated_bookings)
    # Update the kennel with the new list of bookings
    kennel.bookings = updated_bookings
    kennel.save()


def get_bookings_for_user(email: str) -> List:
    # Import Booking and Kennel within the function to avoid circular imports
    from data.bookings import Booking
    from data.kennels import Kennel

    # Retrieve the owner account by email
    owner = Owner.objects(email=email).first()
    if not owner:
        print(f"No owner found with email: {email}")
        return []

    # Retrieve all the dog IDs owned by the user
    dog_ids = owner.dog_ids
    if not dog_ids:
        print(f"Owner with email {email} has no dogs.")
        return []

    # Find all kennels that have bookings for the user's dogs
    kennels_with_bookings = Kennel.objects(bookings__guest_dog_id__in=dog_ids).only('bookings', 'name')

    user_bookings = []
    for kennel in kennels_with_bookings:
        for booking in kennel.bookings:
            if booking.guest_dog_id in dog_ids:
                # Attach the kennel information to the booking
                booking.kennel_name = kennel.name  # Add kennel name directly to booking
                user_bookings.append(booking)

    # Sort bookings by check-in date
    user_bookings.sort(key=lambda b: b.check_in_date)
    return user_bookings


def get_bookings_for_host(email: str) -> List[Booking]:
    # Find the host account using the email
    print("Attempting to get booking")
    print(email)
    account = find_account_by_email(email)

    # Find all kennels owned by the host
    host_kennels = Kennel.objects(id__in=account.kennel_ids).only('bookings', 'name')


    def map_kennel_to_booking(kennel, booking):
        booking.kennel = kennel
        booking.kennel_name = kennel.name
        return booking

    # Extract bookings from the host's kennels
    bookings = [
        map_kennel_to_booking(kennel, booking)
        for kennel in host_kennels
        for booking in kennel.bookings
    ]
    bookings.sort(key=lambda b: b.check_in_date)
    return bookings

def error_msg(text):
    print(Fore.LIGHTRED_EX + text + Fore.WHITE)


def is_kennel_available(kennel: Kennel, checkin: datetime.datetime, checkout: datetime.datetime) -> bool:
    for booking in kennel.bookings:
        if booking.check_in_date < checkout and booking.check_out_date > checkin:
            return False
    return True



def is_kennel_occupied(kennel_id):
    """
    Check if the given kennel is occupied by looking at existing bookings.

    :param kennel_id: The ID of the kennel to check.
    :return: True if the kennel is occupied, False otherwise.
    """
    # Query the parent document that contains the Booking embedded documents.
    # Assuming Kennel is the parent document and Booking is an EmbeddedDocument.

    current_time = datetime.datetime.now()

    # Query all kennels with bookings that overlap the current date.
    kennel = Kennel.objects(id=kennel_id).first()

    if kennel:
        for booking in kennel.bookings:  # Assuming 'bookings' is the list of Booking embedded documents
            if booking.check_in_date <= current_time <= booking.check_out_date:
                return True

    return False
