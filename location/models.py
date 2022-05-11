from django.db import models


# Create your models here.
class Location(models.Model):
    """
    A Location where BSSL conducts business.
    """
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name
