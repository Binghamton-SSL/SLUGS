from django.db import models
from tinymce.models import HTMLField


class Location(models.Model):
    """
    A Location where BSSL conducts business.
    """
    name = models.CharField(max_length=200)
    street_address = HTMLField(blank=True, null=True)
    travel_time_required = models.DecimalField(max_digits=4, decimal_places=2, default=0.0, help_text="Amount of time required to travel to location from BSSL shop measured in HOURS.")

    def __str__(self):
        return self.name
