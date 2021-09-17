from finance.estimate_data_utils import calculateGigCost
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
    status = models.CharField(
        choices=INVOICE_STATUSES,
        max_length=1,
        default="E",
        help_text="Changing the estimate to 'Booked' will publish the gig, and 'Show Concluded' will archive the gig",
    )
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
    outstanding_balance = models.DecimalField(
        max_digits=7, decimal_places=2, blank=True, null=True, default=0.00
    )
    payments_made = models.DecimalField(
        max_digits=7, decimal_places=2, blank=True, null=True, default=0.00
    )

    def save(self):
        self.subtotal = decimal.Decimal(0.00)
        self.fees_amt = decimal.Decimal(0.00)
        self.payment_amt = decimal.Decimal(0.00)

        if self.status == "B":
            self.gig.published = True
        elif self.status == "O":
            self.gig.archived = True

        self.gig.save()

        super().save()

        ret = calculateGigCost(self)

        self.subtotal = ret["subtotal"]
        self.fees_amt = ret["fees_amt"]
        self.payment_amt = ret["payment_amt"]
        self.total_amt = ret["total_amt"]
        self.outstanding_balance = ret["outstanding_balance"]
        self.payments_made = ret["payment_amt"]

        super().save()

    def get_printout_link(self):
        if self.status == "E":
            return format_html(
                "<a href='%s?time=%s'>%s</a>"
                % (
                    reverse("finance:estimate", args=(self.id,)),
                    datetime.now(),
                    "Print Estimate",
                )
            )
        elif self.status == "B":
            return format_html(
                "<a href='%s?time=%s'>%s</a>"
                % (
                    reverse("finance:estimate", args=(self.id,)),
                    datetime.now(),
                    "Print Estimate",
                )
            )
        elif self.status == "Q" or self.status == "A":
            return format_html(
                "<a href='%s?time=%s'>%s</a>"
                % (
                    reverse("finance:invoice", args=(self.id,)),
                    datetime.now(),
                    "Print Invoice",
                )
            )
        else:
            return format_html(
                "<a href='%s?time=%s'>%s</a>"
                "<br>"
                "<a href='%s?time=%s'>%s</a>"
                % (
                    reverse("finance:estimate", args=(self.id,)),
                    datetime.now(),
                    "Print Estimate",
                    reverse("finance:invoice", args=(self.id,)),
                    datetime.now(),
                    "Print Invoice",
                )
            )

    def __str__(self):
        return f"{self.get_status_display()} - {self.gig} - ${self.total_amt}"


class Shift(models.Model):
    time_in = models.DateTimeField()
    time_out = models.DateTimeField(null=True, blank=True)
    total_time = models.DurationField(default=timedelta())
    paid_at = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    cost = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    processed = models.BooleanField(default=False)
    contested = models.BooleanField(default=False)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    override_pay_period = models.ForeignKey(
        "PayPeriod", on_delete=models.PROTECT, null=True, blank=True
    )

    def save(self, *args, **kwargs):
        self.total_time = timedelta()
        if self.paid_at is None:
            self.paid_at = self.content_object.position.hourly_rate.hourly_rate
        if self.time_in and self.time_out:
            self.total_time = self.time_out - self.time_in
            self.cost = (
                round(self.total_time / timezone.timedelta(minutes=15)) / 4
            ) * float(self.paid_at)
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
            f"<div style='margin: .25rem 0 .25rem 0'><a href='{reverse('finance:summary', args=[self.pk])}'>Print Summary</a><br><a href='{reverse('finance:summary_csv', args=[self.pk])}'>Summary CSV File</a></div><br>"
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
        return format_html(
            "".join(
                [
                    (
                        f"<div style='margin: .25rem 0 .25rem 0'>"
                        f"<a href='{reverse('finance:timesheet', args=[self.pk, emp.pk])}'>Get Timesheet: {emp}</a>"
                        # f"<br><a style='margin-top: .25rem' href='{reverse('finance:rollover', args=[self.pk, emp.pk])}'>Rollover Timesheet</a>" # noqa
                        f"</div><br>"
                    )
                    for emp in emps
                ]
            )
        )

    def save(self):
        super().save()
        self.shifts.set(
            Shift.objects.filter(
                (
                    Q(time_in__gte=self.start)
                    & Q(time_out__lte=self.end + timezone.timedelta(days=1))
                    & Q(override_pay_period=None)
                )
                | Q(override_pay_period=self)
            ).order_by("-time_out")
        )
        super().save()

    def __str__(self):
        return f"{self.start} - {self.end} (Paid {self.payday})"


class Payment(models.Model):
    PAYMENT_TYPES = [
        ("C", "Cash"),
        ("H", "Check"),
        ("G", "Grant"),
        ("O", "Other"),
        ("D", "Discount"),
    ]
    payment_date = models.DateField(blank=True, null=True)
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    payment_type = models.CharField(choices=PAYMENT_TYPES, max_length=1)
    estimate = models.ForeignKey("Estimate", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.payment_date} - ${self.amount}"
