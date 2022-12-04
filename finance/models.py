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

from utils.models import PricingMixin


class Wage(PricingMixin, models.Model):
    """
    A pay rate that is earned by an employee. These are tracked over time.
    """
    name = models.CharField(max_length=64)

    def __init__(self, *args, **kwargs):
        self.pricing_set = self.hourlyrate_set
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.name


class Pricing(models.Model):
    date_active = models.DateField(default=date.today)
    date_inactive = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.date_active.strftime('%m.%d.%y')}{'-'+str(self.date_inactive.strftime('%m.%d.%y')) if self.date_inactive else '-Present'}"

    def clean(self, *args, **kwargs):
        if "item_set" not in kwargs:
            raise ValidationError(
                "Pricing validation not implemented on this model. Please contact the developer."
            )
        # if self.date_inactive:
        #     if kwargs['item_set'].filter(
        #         ~Q(pk=self.pk)
        #         &
        #         (
        #             # Before Into
        #             Q(
        #                 date_active__lte=self.date_active,
        #                 date_inactive__gte=self.date_active
        #             )
        #             |
        #             # Entirely during the period
        #             Q(
        #                 date_active__gte=self.date_active,
        #                 date_inactive__lte=self.date_inactive
        #             )
        #             |
        #             # Starts during period, ends after
        #             Q(
        #                 date_active__lte=self.date_inactive,
        #                 date_inactive__gte=self.date_inactive
        #             )
        #         )
        #     ).count() > 0:
        #         raise ValidationError("Pricing overlaps with another period")
        # else:
        #     if kwargs['item_set'].filter(
        #         ~Q(pk=self.pk)
        #         &
        #         (
        #             # Before Into no end date
        #             Q(
        #                 date_active__lte=self.date_active,
        #                 date_inactive=None,
        #             )
        #             |
        #             # Before Into end date
        #             Q(
        #                 date_active__lte=self.date_active,
        #                 date_inactive__gte=self.date_active
        #             )
        #             |
        #             # Start after this
        #             Q(
        #                 date_active__gte=self.date_active
        #             )
        #         )
        #     ).count() > 0:
        #         raise ValidationError("Pricing overlaps with another period")
        del kwargs["item_set"]
        super().clean(*args, **kwargs)


class HourlyRate(models.Model):
    """
    A pay rate for a particular time period
    """
    wage = models.ForeignKey(Wage, on_delete=models.CASCADE)
    hourly_rate = models.DecimalField(decimal_places=2, max_digits=5)
    date_active = models.DateField(default=date.today)
    date_inactive = models.DateField(blank=True, null=True)


class BasePricing(Pricing):
    base_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{('$'+str(self.base_price)+' ') if self.base_price else ''} {('$'+str(self.price_per_hour)+'/hr ') if self.price_per_hour else ''}{super().__str__()}"


class SystemPricing(BasePricing):
    """
    The pricing for a system. Tracked over time
    """
    system = models.ForeignKey("equipment.System", on_delete=models.CASCADE)

    def clean(self, *args, **kwargs):
        kwargs["item_set"] = self.__class__.objects.filter(system=self.system)
        super().clean(*args, **kwargs)


class SystemAddonPricing(BasePricing):
    """
    The pricing for a system addon. Tracked over time
    """
    addon = models.ForeignKey("equipment.SystemAddon", on_delete=models.CASCADE)
    price_per_hour_for_load_in_out_ONLY = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.00, help_text="Price per hour from first dept load in to last dept load out"
    )
    price_per_hour_for_show_ONLY = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.00, help_text="Price per hour from setup by time to end of show"
    )

    def clean(self, *args, **kwargs):
        kwargs["item_set"] = self.__class__.objects.filter(addon=self.addon)
        super().clean(*args, **kwargs)


class VendorEquipmentPricing(BasePricing):
    equipment = models.ForeignKey("equipment.VendorEquipment", on_delete=models.CASCADE)

    def clean(self, *args, **kwargs):
        kwargs["item_set"] = self.__class__.objects.filter(equipment=self.equipment)
        super().clean(*args, **kwargs)


class Fee(PricingMixin, models.Model):
    """
    A predefined fee. Name is from a deprecated version of fees on Gigs.
    """
    def __init__(self, *args, **kwargs):
        self.pricing_set = self.feepricing_set
        super().__init__(*args, **kwargs)

    name = models.CharField(max_length=64)
    description = models.CharField(max_length=512, blank=True, null=True)

    class Meta:
        verbose_name = "Predefined Fee"

    def __str__(self):
        return f"{self.name} - {f'${self.get_current_price().amount}' if self.get_current_price() and self.get_current_price().amount else f'{self.get_current_price().percentage}%' if self.get_current_price() and self.get_current_price().percentage else ''}"  # noqa


class FeePricing(Pricing):
    """
    The pricing for a Free over time.
    """
    fee = models.ForeignKey(Fee, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def clean(self, *args, **kwargs):
        kwargs["item_set"] = self.__class__.objects.filter(fee=self.fee)
        super().clean(*args, **kwargs)


class BaseFee(models.Model):
    name = models.CharField(max_length=64, blank=True, null=True)
    amount = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    description = models.CharField(max_length=512, blank=True, null=True)


class OneTimeFee(models.Model):
    """
    A Fee as applied to a particular Estimate.
    """
    prepared_fee = models.ForeignKey(
        Fee,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text="Auto-fill the fee with a prepared fee",
    )
    estimate = models.ForeignKey("finance.Estimate", on_delete=models.CASCADE)
    name = models.CharField(max_length=64, blank=True, null=True)
    amount = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    description = models.CharField(max_length=512, blank=True, null=True)
    order = models.PositiveIntegerField(default=0, blank=False, null=False)

    class Meta:
        verbose_name = "Fee"
        ordering = ["order"]

    def or_create_your_own(self):
        return ""

    def save(self, *args, **kwargs):
        if self.prepared_fee:
            pricing = self.prepared_fee.get_price_at_date(self.estimate.gig.start)
            self.name = self.prepared_fee.name
            self.amount = pricing.amount
            self.percentage = pricing.percentage
            self.description = self.prepared_fee.description
        super().save(*args, **kwargs)
        self.estimate.save()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.estimate.save()

    def __str__(self):
        return f"{self.name} - {f'${self.amount}' if self.amount else f'{self.percentage}%' if self.percentage else ''}"  # noqa


class VendorFee(BaseFee):
    equipment_order = models.ForeignKey("gig.SubcontractedEquipment", on_delete=models.CASCADE)


class Estimate(models.Model):
    """
    An Estimate generated for a Client of a BSSL Gig. Invoices are also generated from Estimates.
    """
    INVOICE_STATUSES = [
        ("E", "Estimate"),
        ("B", "Booked"),
        ("L", "In Limbo/Postponed"),
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
    estimate_id = models.CharField(max_length=10, default="")

    def save(self):
        self.subtotal = decimal.Decimal(0.00)
        self.fees_amt = decimal.Decimal(0.00)
        self.payment_amt = decimal.Decimal(0.00)
        self.estimate_id = f"E{2500+int(self.pk)}" if self.pk else ""

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
        return f"{self.get_status_display()}{f' (OB: ${self.outstanding_balance})' if (self.outstanding_balance != 0 and self.status == 'A') else ''} - {self.gig} - ${self.total_amt}"


class CannedNote(models.Model):
    """
    A predefined note commonly applied to an Estimate.
    """
    name = models.CharField(max_length=100)
    ordering = models.PositiveIntegerField(default=0)
    note = HTMLField()

    def __str__(self):
        return self.name


class Shift(models.Model):
    """
    A shift worked by a BSSL employee. Linked to a Job, Training, or Office Hour object
    """
    time_in = models.DateTimeField()
    time_out = models.DateTimeField(null=True, blank=True)
    total_time = models.DurationField(default=timedelta())
    paid_at = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    description = models.CharField(
        max_length=150,
        blank=True,
        help_text="Only required if abnormal shift needs explanation to finance",
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

    def clean(self, *args, **kwargs):
        # add custom validation here
        super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.total_time = timedelta()
        if ((self.paid_at is None or self.paid_at == 0.00) and self.content_object is not None):
            self.paid_at = self.content_object.position.hourly_rate.get_price_at_date(
                self.time_in
            ).hourly_rate
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


class TimeSheet(models.Model):
    """
    A timesheet generated as a result of working during a given pay period. 
    """
    def user_dir_path(instance, filename):
        fileName, fileExtension = os.path.splitext(filename)
        return f"uploads/{instance.employee.bnum}/{instance.employee.bnum}_{instance.employee.first_name[0].upper()}{instance.employee.last_name}_TimeSheet_{instance.pay_period.start}_{instance.pay_period.end}{fileExtension}"  # noqa

    employee = models.ForeignKey("employee.Employee", on_delete=models.PROTECT)
    pay_period = models.ForeignKey(
        "PayPeriod", on_delete=models.PROTECT, related_name="pay_period"
    )
    paid_during = models.ForeignKey(
        "PayPeriod",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Use this to override the Pay Period during which the timesheet was paid. Defaults to the Pay Period during which shifts took place.",
        related_name="paid_during",
    )
    signed = models.DateField(blank=True, null=True)
    processed = models.DateField(blank=True, null=True)
    available_to_auto_sign = models.BooleanField(default=False)
    pdf = models.FileField(upload_to=user_dir_path, blank=True, null=True)

    def printout_link(self):
        return format_html(
            (
                f"<div style='margin: .25rem 0 .25rem 0'>"
                f"<a href='{reverse('finance:timesheet', args=[self.pay_period.pk, self.employee.pk])}'>Get Timesheet: {self.employee}</a>"
                # f"<br><a style='margin-top: .25rem' href='{reverse('finance:rollover', args=[self.pk, emp.pk])}'>Rollover Timesheet</a>" # noqa
                f"</div><br>"
            )
        )
    
    def get_admin_url(self):
        return reverse(
            "admin:%s_%s_change" % (self._meta.app_label, self._meta.model_name),
            args=(self.id,),
        )

    def save(self, *args, **kwargs):
        if self.paid_during is None:
            self.paid_during = self.pay_period
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} - {self.pay_period}"


class PayPeriod(models.Model):
    """
    A Pay Period during which employees are paid for their work.
    """
    start = models.DateField()
    end = models.DateField()
    payday = models.DateField()
    submitted = models.DateField(
        blank=True,
        null=True,
        help_text="All timesheets currently unprocessed but signed paid during this pay period will be processed on this date upon save.",
    )
    shifts = models.ManyToManyField("finance.Shift")

    def get_summary(self):
        return format_html(
            f"<div style='margin: .25rem 0 .25rem 0'><a href='{reverse('finance:summary', args=[self.pk])}?time={datetime.now()}'>Print Summary</a><br><a href='{reverse('finance:summary_csv', args=[self.pk])}?time={datetime.now()}'>Summary CSV File</a></div><br>"
        )  # noqa

    def get_paychex_summary(self):
        tms = TimeSheet.objects.filter(paid_during=self.pk, employee__paychex_flex_workerID=None).exclude(signed=None).order_by('employee__last_name')
        return format_html(
            f'''
                <div style='margin: .25rem 0 .25rem 0'>
                    {"".join([f'{tm.employee} Does <b><u>NOT</u></b> have a PayChex Employee ID<br>' for tm in tms])}
                    {"<b>THIS EXPORT WILL NOT BE ABLE TO IMPORT INTO PAYCHEX PROPERLY UNTIL YOU REMOVE THE ROWS MISSING WORKER IDs</b><br>" if tms.count() > 0 else ""}
                    <br>
                    <a href='{reverse('finance:summary_paychex_csv', args=[self.pk])}?time={datetime.now()}'>Download Paychex Flex Payroll Export</a>
                </div>
            '''
        )

    def associated_shifts(self):
        ret = ""
        for shift in self.shifts.all().order_by("processed"):
            ret += f"<div style='margin: .25rem 0 .25rem 0'><a href='{shift.get_admin_url()}'>{shift}</a></div><br>"
        return format_html(ret)

    def timesheets_for_this_pay_period(self):
        timesheets = TimeSheet.objects.filter(paid_during=self.pk).order_by('employee__last_name')
        return format_html(
            "".join(
                [
                    (
                        f"<div style='margin: .25rem 0 .25rem 0'>"
                        f"<a href='{reverse('finance:timesheet', args=[timesheet.pay_period.pk, timesheet.employee.pk])}'>Get Timesheet: {timesheet.employee} {'<b>- SIGNED</b>' if timesheet.signed else ''}{(' - ('+str(timesheet.pay_period)+')') if timesheet.pay_period.pk is not self.pk else ''}</a>"
                        f"</div><br>"
                    )
                    for timesheet in timesheets
                ]
            )
        )

    def save(self):
        super().save()
        self.shifts.set(
            Shift.objects.filter(
                (
                    Q(time_in__gte=self.start)
                    & Q(time_in__lte=self.end + timezone.timedelta(days=1))
                    & Q(override_pay_period=None)
                )
                | Q(override_pay_period=self)
            ).order_by("-time_out")
        )
        super().save()
        emps = []
        for shift in self.shifts.all():
            if shift.content_object.employee not in emps and shift.content_object.employee is not None:
                emps.append(shift.content_object.employee)
        for emp in emps:
            timesheet, created = TimeSheet.objects.get_or_create(
                employee=emp,
                pay_period_id=self.pk,
            )
        if self.submitted:
            TimeSheet.objects.filter(paid_during=self.pk, processed=None).exclude(
                signed=None
            ).update(processed=self.submitted)

    def __str__(self):
        return f"{self.start} - {self.end} (Paid {self.payday})"


class Payment(models.Model):
    """
    A Payment made by a group on their invoice.
    """
    PAYMENT_TYPES = [
        ("C", "Cash"),
        ("H", "Check"),
        ("I", "SA Intra-Organization Transfer"),
        ("G", "Grant"),
        ("O", "Other"),
        ("D", "Discount"),
    ]
    payment_date = models.DateField(blank=True, null=True)
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    payment_type = models.CharField(choices=PAYMENT_TYPES, max_length=1)
    estimate = models.ForeignKey("Estimate", on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.estimate.save()
        
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.estimate.save()

    def __str__(self):
        return f"{self.payment_date} - ${self.amount}"

    class Meta:
        verbose_name = "Incoming Payment"