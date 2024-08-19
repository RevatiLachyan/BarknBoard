import datetime
import mongoengine

from data.bookings import Booking


class Kennel(mongoengine.Document):
    registered_date = mongoengine.DateTimeField(default=datetime.datetime.now)

    name = mongoengine.StringField(required=True)
    price = mongoengine.FloatField(required=True)
    size = mongoengine.IntField(required=True, choices=[0, 1, 2])  # 0 = Small, 1 = Medium, 2 = Large
    has_toys = mongoengine.BooleanField(required=True)
    allow_unsocial_dogs = mongoengine.BooleanField(default=False)

    bookings = mongoengine.EmbeddedDocumentListField(Booking)

    meta = {
        'db_alias': 'core',
        'collection': 'kennels'
    }
