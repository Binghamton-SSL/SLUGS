from django.db import models
import gig.models as gigModels
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import inch
from django.core.files.storage import FileSystemStorage
from datetime import date
from django.conf import settings


def generateInvoice(invoice):
    pass

# Create your models here.
class Timesheet(models.Model):
    pass

class PayrollSheet(models.Model):
    pass

class Fee(models.Model):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    description = models.CharField(max_length=100)

    def __str__(self):
        num = str(self.amount) if self.amount else str(self.percentage)+"%"
        return self.name + " - " + num

class Invoice(models.Model):
    # Linked Fees, 
    STATUS_TYPES = [
        ("E", 'Estimate'),
        ("B", 'Booked'),
        ("A", 'Awaiting Payment'),
        ("C", 'Closed'),
    ]
    status = models.CharField(choices=STATUS_TYPES,max_length=1, null=True, default='E')
    linked_gig = models.ForeignKey(gigModels.Gig, on_delete=models.PROTECT)
    payment_due_date = models.DateField(null=True, blank=True)
    date_created = models.DateField(auto_now_add=True,blank=True)
    date_paid = models.DateField(blank=True,null=True)
    fees = models.ManyToManyField(
        Fee,
        blank=True,
        help_text="All fees are added to total when invoice is generated <br>"
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    def __str__(self):
        return self.status +" - "+ str(self.linked_gig)

    def save(self, *args, **kwargs):
        self.subtotal = 0
        self.total = 0
        for system in gigModels.SystemInstance.objects.filter(linked_gig=self.linked_gig):
            self.subtotal = self.subtotal + system.system.base_price if system.system.base_price else self.subtotal + system.system.price_per_hour*system.hours_rented
        for fee in self.fees.all():
            self.total = self.total + fee.amount if fee.amount else self.total + fee.percentage*self.subtotal/100
        self.total = self.total + self.subtotal
        super().save(*args, **kwargs)
