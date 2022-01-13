from datetime import datetime
from django.db import models
from gig.models import DEPARTMENTS
import employee.models as employee
from django.db.models import Q

from utils.models import PricingMixin


# Create your models here.
class System(PricingMixin, models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=1024, blank=True, null=True)
    department = models.CharField(max_length=1, choices=DEPARTMENTS)

    def __init__(self, *args, **kwargs):
        self.pricing_set = self.systempricing_set
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.department + " - " + self.name


class SystemAddon(PricingMixin, models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=1024, blank=True, null=True)
    department = models.CharField(max_length=1, choices=DEPARTMENTS)

    def __init__(self, *args, **kwargs):
        self.pricing_set = self.systemaddonpricing_set
        super().__init__(*args, **kwargs)

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
