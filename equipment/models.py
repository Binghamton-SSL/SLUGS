from datetime import datetime
from django.db import models
from gig.models import DEPARTMENTS
import employee.models as employee
from django.db.models import Q
from datetime import date

from utils.models import PricingMixin


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    class Meta:
         verbose_name_plural = "Categories"

class Equipment(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=1024, blank=True, null=True)
    brand = models.CharField(max_length=200, blank=True, null=True)
    model_number = models.CharField(max_length=200, blank=True, null=True)
    department = models.CharField(max_length=1, choices=DEPARTMENTS)
    value = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    wattage = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    purchase_date = models.DateField(default=date.today, help_text="Date of purchase or creation if made")
    reorder_link = models.URLField(blank=True)

    def __str__(self):
        if not self.brand:
            return f"{self.name}"

        return f"{self.name} ({self.brand})"

    class Meta:
         verbose_name_plural = "Equipment"


class System(PricingMixin, models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=1024, blank=True, null=True)
    department = models.CharField(max_length=1, choices=DEPARTMENTS)
    equipment = models.ManyToManyField(Equipment, through="SystemQuantity")

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


# new models
class Item(models.Model):
    serial_no = models.CharField(max_length=200)
    item_type = models.ForeignKey(Equipment, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.item_type} #{self.serial_no}"


class ServiceRecord(models.Model):
    name = models.CharField(max_length=200)
    date_created = models.DateField(auto_now_add=True)
    date_last_modified = models.DateField(auto_now=True)
    note = models.TextField()
    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} on {self.date_created}"


class BaseQuantity(models.Model):
    """Through model linking System and Equipment quantity"""
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.equipment}, Quantity: {self.quantity}, "


class SystemQuantity(BaseQuantity):
    system = models.ForeignKey(System, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Equipment Quantity"
        verbose_name_plural = "Equipment Quantities"

    def __str__(self):
        return super().__str__() + f"System: {self.system}"


class SystemQuantityAddon(BaseQuantity):
    system_addon = models.ForeignKey(SystemAddon, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Addon Equipment Quantity"
        verbose_name_plural = "Addon Equipment Quantities"

    def __str__(self):
        return super().__str__() + f"System: {self.system}"
