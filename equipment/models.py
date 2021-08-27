from django.db import models
from gig.models import DEPARTMENTS
import employee.models as employee


# Create your models here.
class System(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=1024, blank=True, null=True)
    department = models.CharField(max_length=1, choices=DEPARTMENTS)
    base_price = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True
    )
    price_per_hour = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True
    )

    def __str__(self):
        return self.department + " - " + self.name


class SystemAddon(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=1024, blank=True, null=True)
    department = models.CharField(max_length=1, choices=DEPARTMENTS)
    base_price = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True
    )
    price_per_hour = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True
    )

    def __str__(self):
        return self.name


class BrokenEquipmentReport(models.Model):
    CASE_TYPES = [
        ("U", "Unread"),
        ("A", "Acknowledged"),
        ("W", "WIP"),
        ("B", "Blocked"),
        ("C", "Closed"),
    ]
    broken_system = models.ForeignKey(System, on_delete=models.CASCADE)
    date_filed = models.DateTimeField(auto_now_add=True)
    reported_broken_by = models.ForeignKey(employee.Employee, models.PROTECT, null=True)
    notes = models.TextField()
    investigation = models.TextField(null=True, blank=True)
    status = models.CharField(choices=CASE_TYPES, max_length=1, null=True)

    def __str__(self):
        return self.status + " - " + str(self.broken_system)
