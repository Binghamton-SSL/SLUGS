from django.db import models
from gig.models import DEPARTMENTS
from client.models import Contact
import employee.models as employee
from datetime import date
from tinymce.models import HTMLField

from utils.models import PricingMixin


# Create your models here.
class Category(models.Model):
    """
    A Category of Equipment at BSSL
    """
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Equipment(models.Model):
    """
    A piece of Equipment at BSSL. May have multiple instances called Items.
    """
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=1024, blank=True, null=True)
    brand = models.CharField(max_length=200, blank=True, null=True)
    model_number = models.CharField(max_length=200, blank=True, null=True)
    department = models.CharField(max_length=1, choices=DEPARTMENTS)
    value = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    wattage = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    reorder_link = models.URLField(blank=True)

    def __str__(self):
        if not self.brand:
            return f"{self.name}"

        return f"{self.name} ({self.brand})"

    class Meta:
        verbose_name_plural = "Equipment"


class System(PricingMixin, models.Model):
    """
    A BSSL system rented out to a client
    """
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
    """
    A BSSL system addon rented out to a client
    """
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=1024, blank=True, null=True)
    department = models.CharField(max_length=1, choices=DEPARTMENTS)

    def __init__(self, *args, **kwargs):
        self.pricing_set = self.systemaddonpricing_set
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.name


class BrokenEquipmentReport(models.Model):
    """
    A report filed by an Employee during a Gig
    """
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
    """
    An instance of a piece of Equipment BSSL owns
    """
    ITEM_STATUS = [
        ("R", "In Box/Reserves"),
        ("O", "Operational"),
        ("B", "Broken"),
        ("S", "Sold"),
        ("M", "RMA'd"),
        ("D", "Discarded"),
        ("U", "Unknown"),
        ("X", "Other"),
    ]
    status = models.CharField(max_length=1, choices=ITEM_STATUS, default="O")
    label = models.CharField(max_length=200, blank=True, null=True)
    serial_no = models.CharField(max_length=200)
    purchase_date = models.DateField(
        default=date.today, help_text="Date of purchase or creation if made"
    )
    item_type = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    barcode = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        unique=True,
        help_text="If no serial number barcode is present on device upon arrival leave blank + print and affix barcode generated on save. Otherwise enter barcode text on device if unique.",
    )
    children = models.ManyToManyField("Item", through="ItemRelationship", blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.barcode is None and self.pk is not None:
            self.barcode = f"BSSL-{self.pk}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item_type} #{self.serial_no}"


class ItemRelationship(models.Model):
    """
    The relationship between an item and another.
    """
    parent = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="parent_item"
    )
    child = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="child_item")

    def __str__(self):
        return f"{self.parent} -> {self.child}"


class ServiceRecord(models.Model):
    """
    A service record on a piece of equipment
    """
    name = models.CharField(max_length=200)
    date_created = models.DateField(auto_now_add=True)
    date_last_modified = models.DateField(auto_now=True)
    note = models.TextField()
    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} on {self.date_created}"

    class Meta:
        verbose_name = "Service Record / Equipment Note"
        verbose_name_plural = "Service Records & Equipment Notes"


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


class Vendor(Contact):
    website = models.CharField(max_length=512, null=True, blank=True)
    physical_address = HTMLField(blank=True, null=True)


class VendorEquipment(PricingMixin, models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    name = models.CharField(max_length=512)
    description = models.CharField(max_length=512, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.get_current_price()} - {self.vendor}"

    def __init__(self, *args, **kwargs):
        self.pricing_set = self.vendorequipmentpricing_set
        super().__init__(*args, **kwargs)
    
    class Meta:
        verbose_name_plural = "Vendor Equipment"