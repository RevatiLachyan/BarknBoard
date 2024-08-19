from typing import List, Optional
import datetime
from colorama import Fore
import bson

from data.bookings import Booking
from data.kennels import Kennel
from data.owners import Owner
from data.dogs import Dog


def create_account(name: str, email: str) -> Owner:
    owner = Owner()
    owner.name = name
    owner.email = email

    owner.save()

    return owner


def find_account_by_email(email: str) -> Owner:
    owner = Owner.objects(email=email).first()
    return owner


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


def find_kennels_for_user(account: Owner) -> List[Kennel]:
    query = Kennel.objects(id__in=account.kennel_ids)
    kennels = list(query)

    return kennels


def add_available_date(kennel: Kennel,
                       start_date: datetime.datetime, days: int) -> Kennel:
    booking = Booking()
    booking.check_in_date = start_date
    booking.check_out_date = start_date + datetime.timedelta(days=days)

    kennel = Kennel.objects(id=kennel.id).first()
    kennel.bookings.append(booking)
    kennel.save()

    return kennel


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


def get_dogs_for_user(user_id: bson.ObjectId) -> List[Dog]:
    owner = Owner.objects(id=user_id).first()
    dogs = Dog.objects(id__in=owner.dog_ids).all()

    return list(dogs)


def get_available_kennels(checkin: datetime.datetime,
                          checkout: datetime.datetime, dog: Dog) -> List[Kennel]:
    # Ensure the kennel size is suitable for the dog
    query = Kennel.objects() \
        .filter(size__gte=dog.size) \
        .filter(bookings__check_in_date__lte=checkin) \
        .filter(bookings__check_out_date__gte=checkout)

    if dog.is_unsocial:
        query = query.filter(allow_unsocial_dogs=True)

    # Order by price and size to prioritize more affordable kennels
    kennels = query.order_by('price', '-size')

    final_kennels = []
    for c in kennels:
        for b in c.bookings:
            # Ensure the kennel is available during the requested dates
            if b.check_in_date <= checkin and b.check_out_date >= checkout and b.guest_dog_id is None:
                final_kennels.append(c)
                break  # No need to check other bookings for this kennel if it fits the criteria

    return final_kennels


def book_kennel(account, dog, kennel, checkin, checkout):
    booking: Optional[Booking] = None

    if kennel.size < dog.size:
        error_msg("Kennel size is smaller than your dog's size")

    for b in kennel.bookings:
        if b.check_in_date <= checkin and b.check_out_date >= checkout and b.guest_dog_id is None:
            booking = b
            break

    booking.guest_owner_id = account.id
    booking.guest_dog_id = dog.id
    booking.check_in_date = checkin
    booking.check_out_date = checkout
    booking.booked_date = datetime.datetime.now()

    kennel.save()


def get_bookings_for_user(email: str) -> List[Booking]:
    account = find_account_by_email(email)

    booked_kennels = Kennel.objects() \
        .filter(bookings__guest_owner_id=account.id) \
        .only('bookings', 'name')

    def map_kennel_to_booking(kennel, booking):
        booking.kennel = kennel
        return booking

    bookings = [
        map_kennel_to_booking(kennel, booking)
        for kennel in booked_kennels
        for booking in kennel.bookings
        if booking.guest_owner_id == account.id
    ]

    return bookings


def error_msg(text):
    print(Fore.LIGHTRED_EX + text + Fore.WHITE)
