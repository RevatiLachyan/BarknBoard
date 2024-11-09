import mongoengine

from data.dogs import Dog
from mongoengine import LazyReferenceField


class Booking(mongoengine.EmbeddedDocument):
    kennel = LazyReferenceField('Kennel')
    kennel_id = mongoengine.ObjectIdField()
    guest_owner_id = mongoengine.ObjectIdField()
    guest_dog_id = mongoengine.ObjectIdField()

    booked_date = mongoengine.DateTimeField()
    check_in_date = mongoengine.DateTimeField(required=True)
    check_out_date = mongoengine.DateTimeField(required=True)

    review = mongoengine.StringField()
    rating = mongoengine.IntField(default=0)

    @property
    def dog(self):
        return Dog.objects(id=self.guest_dog_id).first()

    @property
    def duration_in_days(self):
        dt = self.check_out_date - self.check_in_date
        return dt.days

