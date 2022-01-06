from finance.estimate_data_utils import calculateGigCost
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Q
import django.utils.timezone as timezone
from datetime import timedelta, datetime, date
from django.db import models
from django.contrib.auth.models import Group
from tinymce.models import HTMLField
import decimal
from django.core.validators import ValidationError


class Wage(models.Model):
    name = models.CharField(max_length=64)

    def get_current_rate(self):
        return self.hourlyrate_set.filter(
            Q(date_active__lte=datetime.now())
            &
            (
                Q(date_inactive__gt=datetime.now())
                |
                Q(date_inactive=None)
            )
        ).first()

    def get_is_active(self):
        return True if self.get_current_rate() is not None else False

    def get_active_rate(self):
        current = self.get_current_rate()
        return current if current else self.hourlyrate_set.order_by("date_inactive").last()

    def get_rate_at_date(self, date):
        return self.hourlyrate_set.filter(
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
        # return f"{self.name} - ${self.get_active_rate().hourly_rate}/hr"


class Pricing(models.Model):
    date_active = models.DateField(default=date.today)
    date_inactive = models.DateField(blank=True, null=True)


class HourlyRate(models.Model):
    wage = models.ForeignKey(Wage, on_delete=models.CASCADE)
    hourly_rate = models.DecimalField(decimal_places=2, max_digits=5)
    date_active = models.DateField(default=date.today)
    date_inactive = models.DateField(blank=True, null=True)


class BasePricing(Pricing):
    base_price = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.00
    )
    price_per_hour = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.00
    )


class SystemPricing(BasePricing):
    system = models.ForeignKey("equipment.System", on_delete=models.CASCADE)


class SystemAddonPricing(BasePricing):
    addon = models.ForeignKey("equipment.SystemAddon", on_delete=models.CASCADE)
    price_per_hour_for_load_in_out_ONLY = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.00
    )


class Fee(models.Model):
    name = models.CharField(max_length=64)
    amount = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    description = models.CharField(max_length=512, blank=True, null=True)
    ordering = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Relative order of fee, 0 is top importance. Does not have to be unique. I suggest\n 0=before booking, 1=during booking, 2=during show, 3=during invoice, 4=after invoice.",
    )

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
        ("N", "Abandoned"),
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
    canned_notes = models.ManyToManyField(
        "CannedNote",
        blank=True,
        help_text="These notes will appear above any notes you enter manually below. These are common notes added to estimates.",
    )
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
        max_digits=7,
        decimal_places=2,
        null=True,
        default=0.00,
        help_text="Only use in cases where there is a numerical descrepency that cannot be traced. For all discounts, refunds, and clerical errors, input a 'One Time Fee'",
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


class CannedNote(models.Model):
    name = models.CharField(max_length=100)
    ordering = models.PositiveIntegerField(default=0)
    note = HTMLField()

    def __str__(self):
        return self.name


class Shift(models.Model):
    time_in = models.DateTimeField()
    time_out = models.DateTimeField(null=True, blank=True)
    total_time = models.DurationField(default=timedelta())
    paid_at = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    description = models.CharField(
        max_length=150,
        blank=True,
        help_text="Only required if abnormal shift needs explaination to finance",
    )
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
        if self.paid_at is None or self.paid_at == 0.00:
            self.paid_at = self.content_object.position.hourly_rate.get_rate_at_date(self.time_in).hourly_rate
        if self.description is None:
            self.description = self.__str__()
        if self.time_in and self.time_out:
            self.total_time = self.time_out - self.time_in
            self.cost = (
                round(self.total_time / timezone.timedelta(minutes=15)) / 4
            ) * float(self.paid_at)

        # Validation: Shift cannot be negative time
        if self.cost < 0:
            raise ValidationError("Shift cannot be negative payout.")
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
Group.add_to_class("description", models.TextField(blank=True, null=True))


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
        emps = []
        for shift in self.shifts.all():
            if shift.content_object.employee not in emps:
                emps.append(shift.content_object.employee)
        for emp in emps:
            timesheet, created = TimeSheet.objects.get_or_create(
                employee=emp,
                pay_period_id=self.pk,
            )

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


class TimeSheet(models.Model):
    def user_dir_path(instance, filename):
        fileName, fileExtension = os.path.splitext(filename)
        return f"uploads/{instance.employee.bnum}/{instance.employee.bnum}_{instance.employee.first_name[0].upper()}{instance.employee.last_name}_TimeSheet_{instance.pay_period.start}_{instance.pay_period.end}{fileExtension}"  # noqa

    employee = models.ForeignKey("employee.Employee", on_delete=models.PROTECT)
    pay_period = models.ForeignKey("PayPeriod", on_delete=models.PROTECT, related_name="pay_period")
    paid_during = models.ForeignKey("PayPeriod", on_delete=models.PROTECT, null=True, blank=True, help_text="Use this to override the Pay Period during which the timesheet was paid. Defaults to the Pay Period during which shifts took place.", related_name="paid_during")
    signed = models.DateField(blank=True, null=True)
    processed = models.DateField(blank=True, null=True)
    available_to_auto_sign = models.BooleanField(default=False)
    pdf = models.FileField(upload_to=user_dir_path, blank=True, null=True)

    def printout_link(self):
        return format_html((
                        f"<div style='margin: .25rem 0 .25rem 0'>"
                        f"<a href='{reverse('finance:timesheet', args=[self.pay_period.pk, self.employee.pk])}'>Get Timesheet: {self.employee}</a>"
                        # f"<br><a style='margin-top: .25rem' href='{reverse('finance:rollover', args=[self.pk, emp.pk])}'>Rollover Timesheet</a>" # noqa
                        f"</div><br>"
        ))

    def save(self, *args, **kwargs):
        if self.paid_during is None:
            self.paid_during = self.pay_period
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} - {self.pay_period}"