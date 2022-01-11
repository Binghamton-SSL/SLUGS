from datetime import datetime
from django.db import models
from gig.models import DEPARTMENTS
import employee.models as employee
from django.db.models import Q
from datetime import date


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Equipment(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=1024, blank=True, null=True)
    brand = models.CharField(max_length=200)
    model_number = models.CharField(max_length=200)
    department = models.CharField(max_length=1, choices=DEPARTMENTS)
    value = models.PositiveIntegerField(default=0)
    wattage = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    purchase_date = models.DateField(default=date.today)
    reorder_link = models.URLField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.brand})"


class System(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=1024, blank=True, null=True)
    department = models.CharField(max_length=1, choices=DEPARTMENTS)
    equipment = models.ManyToManyField(Equipment, through="SystemQuantity")

    def get_current_price(self):
        return self.systempricing_set.filter(
            Q(date_active__lte=datetime.now())
            &
            (
                Q(date_inactive__gt=datetime.now())
                |
                Q(date_inactive=None)
            )
        ).first()

    def get_is_active(self):
        return True if self.get_current_price() is not None else False

    def get_active_price(self):
        current = self.get_current_price()
        return current if current else self.systempricing_set.order_by("date_inactive").last()

    def get_price_at_date(self, date):
        return self.systempricing_set.filter(
            Q(date_active__lte=date)
            &
            (
                Q(date_inactive__gte=date)
                |
                Q(date_inactive=None)
            )
        ).first()

    def __str__(self):
        return self.department + " - " + self.name


class SystemAddon(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=1024, blank=True, null=True)
    department = models.CharField(max_length=1, choices=DEPARTMENTS)

    def get_current_price(self):
        return self.systemaddonpricing_set.filter(
            Q(date_active__lte=datetime.now())
            &
            (
                Q(date_inactive__gt=datetime.now())
                |
                Q(date_inactive=None)
            )
        ).first()

    def get_is_active(self):
        return True if self.get_current_price() is not None else False

    def get_active_price(self):
        current = self.get_current_price()
        return current if current else self.systemaddonpricing_set.order_by("date_inactive").last()

    def get_price_at_date(self, date):
        return self.systemaddonpricing_set.filter(
            Q(date_active__lte=date)
            &
            (
                Q(date_inactive__gte=date)
                |
                Q(date_inactive=None)
            )
        ).first()

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
class ServiceRecord(models.Model):
    name = models.CharField(max_length=200)
    date_created = models.DateField(default=date.today)
    note = models.TextField()

    def __str__(self):
        return f"{self.name} on {self.date_created}"


class Item(models.Model):
    id = models.IntegerField(primary_key=True)
    serial_no = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    service_record = models.ForeignKey(ServiceRecord, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.serial_no}"


class BaseQuantity(models.Model):
    """Through model linking System and Equipment quantity"""
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.equipment}, Quantity: {self.quantity}, "


class SystemQuantity(BaseQuantity):
    system = models.ForeignKey(System, on_delete=models.CASCADE)

    def __str__(self):
        return super().__str__() + f"System: {self.system}"


class SystemQuantityAddon(BaseQuantity):
    system = models.ForeignKey(SystemAddon, on_delete=models.CASCADE)

    def __str__(self):
        return super().__str__() + f"System: {self.system}"
