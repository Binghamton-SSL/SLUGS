from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.html import format_html
from django.core.exceptions import BadRequest
from django.urls import reverse
from django.db.models import Q
import django.utils.timezone as timezone
from datetime import timedelta, datetime
from django.db import models
from django.contrib.auth.models import Group
from gig.models import SystemInstance
from tinymce.models import HTMLField
import decimal


# Create your models here.
class Wage(models.Model):
    name = models.CharField(max_length=64)
    hourly_rate = models.DecimalField(decimal_places=2, max_digits=5)

    def __str__(self):
        return f"{self.name} - ${self.hourly_rate}/hr"


class Fee(models.Model):
    name = models.CharField(max_length=64)
    amount = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    description = models.CharField(max_length=512, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {f'${self.amount}' if self.amount else f'{self.percentage}%' if self.percentage else ''}"  # noqa


class OneTimeFee(models.Model):
    estimate = models.ForeignKey("finance.Estimate", on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    amount = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    description = models.CharField(max_length=512, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {f'${self.amount}' if self.amount else f'{self.percentage}%' if self.percentage else ''}"  # noqa


class Estimate(models.Model):
    INVOICE_STATUSES = [
        ("E", "Estimate"),
        ("B", "Booked"),
	("O", "Show Concluded"),
        ("A", "Awaiting Payment"),
        ("C", "Closed"),
	("X", "Canceled"),
    ]
    status = models.CharField(choices=INVOICE_STATUSES, max_length=1, default="E")
    gig = models.ForeignKey("gig.Gig", on_delete=models.CASCADE)
    billing_contact = models.ForeignKey("client.OrgContact", on_delete=models.PROTECT)
    signed_estimate = models.FileField(upload_to="estimates", null=True, blank=True)
    notes = HTMLField(
        blank=True,
        null=True,
        help_text="These notes will appear on the estimate to be signed by the client.",
    )
    payment_due = models.DateField(blank=True, null=True)
    paid = models.DateField(blank=True, null=True)
    fees = models.ManyToManyField(Fee, blank=True)
    subtotal = models.DecimalField(
        max_digits=7, decimal_places=2, blank=True, null=True, default=0.00
    )
    fees_amt = models.DecimalField(
        max_digits=7, decimal_places=2, blank=True, null=True, default=0.00
    )
    adjustments = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, default=0.00
    )
    total_amt = models.DecimalField(
        max_digits=7, decimal_places=2, blank=True, null=True, default=0.00
    )

    def save(self):
        self.subtotal = decimal.Decimal(0.00)
        self.fees_amt = decimal.Decimal(0.00)

        if self.status == "B":
            self.gig.published = True
        elif self.status == "A":
            self.gig.archived = True
        self.gig.save()

        for system in self.gig.systems.all():
            dept = system.department
            if len(self.gig.loadin_set.all()) < 1:
                raise BadRequest()
            rented_start = (
                self.gig.loadin_set.filter(department=dept)
                .order_by("shop_time")
                .first()
                .shop_time
            )
            rented_end = (
                self.gig.loadin_set.filter(department=dept)
                .order_by("-load_out")
                .first()
                .load_out
            )
            time_rented = rented_end - rented_start
            system_price = round(
                system.base_price
                + (
                    system.price_per_hour
                    * decimal.Decimal(time_rented / timezone.timedelta(hours=1))
                ),
                2,
            )
            addons = SystemInstance.objects.get(
                gig=self.gig, system=system
            ).addoninstance_set.all()
            if len(addons) > 0:
                for addon_set_item in addons:
                    addon = addon_set_item.addon
                    system_price += round(
                        (addon.base_price * addon_set_item.qty)
                        + (
                            addon.price_per_hour
                            * addon_set_item.qty
                            * decimal.Decimal(time_rented / timezone.timedelta(hours=1))
                        ),
                        2,
                    )
            self.subtotal += decimal.Decimal(system_price)
        if self.pk is None:
            super().save()
        for fee in self.onetimefee_set.all():
            self.fees_amt += round(
                fee.amount
                + (
                    decimal.Decimal(fee.percentage / 100 if fee.percentage else 0)
                    * self.subtotal
                ),
                2,
            )
        for fee in self.fees.all():
            self.fees_amt += round(
                fee.amount
                + (
                    decimal.Decimal(fee.percentage / 100 if fee.percentage else 0)
                    * self.subtotal
                ),
                2,
            )
        self.total_amt = self.subtotal + self.fees_amt + self.adjustments
        super().save()

    def get_printout_link(self):
        self.save()
        return format_html(
            "<a href='%s?time=%s'>%s</a>"
            % (reverse("finance:estimate", args=(self.id,)), datetime.now(), "Print Estimate")
        )

    def __str__(self):
        return f"{self.get_status_display()} - {self.gig} - ${self.total_amt}"


class Shift(models.Model):
    time_in = models.DateTimeField()
    time_out = models.DateTimeField(null=True, blank=True)
    total_time = models.DurationField(default=timedelta())
    cost = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    processed = models.BooleanField(default=False)
    contested = models.BooleanField(default=False)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    def save(self, *args, **kwargs):
        self.total_time = timedelta()
        if self.time_in and self.time_out:
            self.total_time = self.time_out - self.time_in
            self.cost = (
                round(self.total_time / timezone.timedelta(minutes=15)) / 4
            ) * float(self.content_object.position.hourly_rate.hourly_rate)
        super().save(*args, **kwargs)

    def get_admin_url(self):
        return reverse(
            "admin:%s_%s_change" % (self._meta.app_label, self._meta.model_name),
            args=(self.id,),
        )

    def __str__(self):
        return f"{self.content_object.employee if self.content_object else ''} - {self.content_object} - {self.total_time} - ${self.cost}"  # noqa


Group.add_to_class(
    "hourly_rate",
    models.ForeignKey(Wage, on_delete=models.PROTECT, null=True, blank=True),
)


class PayPeriod(models.Model):
    start = models.DateField()
    end = models.DateField()
    payday = models.DateField()
    submitted = models.BooleanField(default=False)
    shifts = models.ManyToManyField("finance.Shift")

    def get_summary(self):
        return format_html(
            f"<div style='margin: .25rem 0 .25rem 0'><a href='{reverse('finance:summary', args=[self.pk])}'>Summary</a></div><br>"
        )  # noqa

    def associated_shifts(self):
        ret = ""
        for shift in self.shifts.all():
            ret += f"<div style='margin: .25rem 0 .25rem 0'><a href='{shift.get_admin_url()}'>{shift}</a></div><br>"
        return format_html(ret)

    def associated_employees(self):
        emps = []
        for shift in self.shifts.all():
            if shift.content_object.employee not in emps:
                emps.append(shift.content_object.employee)
        print(emps)
        return format_html(
            "".join(
                [
                    f"<div style='margin: .25rem 0 .25rem 0'><a href='{reverse('finance:timesheet', args=[self.pk, emp.pk])}'>Get Timesheet: {emp}</a></div><br>"  # noqa
                    for emp in emps
                ]
            )
        )

    def save(self):
        super().save()
        self.shifts.set(
            Shift.objects.filter(
                Q(time_in__gte=self.start)
                & Q(time_out__lte=self.end + timezone.timedelta(days=1))
            ).order_by("-time_out")
        )
        super().save()

    def __str__(self):
        return f"{self.start} - {self.end} (Paid {self.payday})"
