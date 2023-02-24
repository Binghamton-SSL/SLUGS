from finance.estimate_data_utils import calculateGigCost
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Q, Count, Sum
import django.utils.timezone as timezone
from datetime import timedelta, datetime, date
from django.db import models
from django.contrib.auth.models import Group
from tinymce.models import HTMLField
import decimal
from django.core.validators import ValidationError
import os

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
    A pay rate for a particular time period. Dates active and inactive are inclusive
    """
    wage = models.ForeignKey(Wage, on_delete=models.CASCADE)
    hourly_rate = models.DecimalField(decimal_places=2, max_digits=5)
    date_active = models.DateField(default=date.today)
    date_inactive = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.wage} ({self.date_active.strftime('%m.%d.%y')}-{self.date_inactive.strftime('%m.%d.%y') if self.date_inactive else 'Present'})) ${self.hourly_rate}"

    def get_shifts_used_in(self, filterset=None):
        shifts_used = filterset.filter(
                    Q(office_hours__position__hourly_rate=self.wage.pk)
                    |
                    Q(job__position__hourly_rate=self.wage.pk)
                    |
                    Q(trainee__position__hourly_rate=self.wage.pk)
                )
        if self.date_inactive:
            shifts_used = shifts_used.filter(
                (
                    Q(time_in__gte=self.date_active)
                    &
                    Q(time_in__lte=self.date_inactive)
                )
            )
        else:
            shifts_used = shifts_used.filter(
                Q(time_in__gte=self.date_active)
            )
        return shifts_used

    def delete(self):
        if self.get_shifts_used_in(Shift.objects.all()).count() > 0:
            raise ValidationError("Cannot delete hourly rate that has been used")

    def clean(self):
        shifts_used = None

        # Validation: Only allow fields to be changed in certain cases
        if self.pk:
            previous = self.__class__.objects.get(pk=self.pk)
            shifts_used = self.get_shifts_used_in(Shift.objects.all())
            # Validation: If used at all, do not allow to change price
            if (previous.hourly_rate != self.hourly_rate):
                if shifts_used.count() > 0:
                    raise ValidationError("Cannot change hourly rate because it is used in shift IDs: " + ", ".join([str(s.pk) for s in shifts_used]))
            # If changing timeframe, check that it does not decrease the amount of shifts covered 
            # Get the number of shifts that are covered by the previous timeframe
            shifts_used_prev = Shift.objects.filter(
                    Q(office_hours__position__hourly_rate=previous.wage.pk)
                    |
                    Q(job__position__hourly_rate=previous.wage.pk)
                    |
                    Q(trainee__position__hourly_rate=previous.wage.pk)
                )
            if previous.date_inactive:
                shifts_used_prev = shifts_used_prev.filter(
                    (
                        Q(time_in__gte=previous.date_active)
                        &
                        Q(time_in__lte=previous.date_inactive)
                    )
                )
            else:
                shifts_used_prev = shifts_used_prev.filter(
                    Q(time_in__gte=previous.date_active)
                )
            # If the two aren't the same set and the previous set has shifts in it that the current set won't, raise an error
            if set(shifts_used_prev) != set(shifts_used) and shifts_used_prev.exclude(pk__in=shifts_used.values('pk')).count() > 0:
                raise ValidationError("Cannot change timeframe because it decreases the number of shifts covered")


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
    reason_contested = models.CharField(max_length=256, blank=True, null=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    override_pay_period = models.ForeignKey(
        "PayPeriod", on_delete=models.PROTECT, null=True, blank=True
    )

    def clean(self, *args, **kwargs):
        # Validation: Shift cannot be negative time
        if self.time_out and self.time_in and self.time_out < self.time_in:
            raise ValidationError("Shift cannot be negative.")

        # Validation: Shift must have reason if contested
        if self.contested and not self.reason_contested:
            raise ValidationError("Shift must have reason if contested.")
        
        # Validation: Shift cannot be approved if it is not in a pay period
        if self.processed and not PayPeriod.objects.filter(start__lte=timezone.localtime(self.time_in).date(), end__gte=timezone.localtime(self.time_in).date()).first():
            raise ValidationError("Shift cannot be approved if there is no pay period within the shift's timeframe.")

        # Validation: Cannot change times of shift once processed
        # (do not apply if processing on this save and check that time in and out do not match)
        prev_values = self.__class__.objects.get(pk=self.pk)
        if self.processed and self.pk and prev_values.processed != False and (prev_values.time_in != self.time_in or prev_values.time_out != self.time_out):
            raise ValidationError("Cannot change times of shift once processed. Please contact the Financial Director.")

    def save(self, *args, **kwargs):
        self.total_time = timedelta()
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

        super().save(*args, **kwargs)
        

        # Add shift to associated timesheet, if it doesn't exist already create it
        # Find pay period (start of pay period to end of date end of pay period)
        pay_period = PayPeriod.objects.filter(start__lte=timezone.localtime(self.time_in).date(), end__gte=timezone.localtime(self.time_in).date()).first()
        if self.processed:
            if self.override_pay_period:
                tm, created = TimeSheet.objects.get_or_create(employee=self.content_object.employee, pay_period=self.override_pay_period)
                tm.shifts.add(self)
            else:
                if pay_period:
                    tm, created = TimeSheet.objects.get_or_create(employee=self.content_object.employee, pay_period=pay_period)
                else:
                    raise ValidationError("Shift must be within a pay period.")
                tm.shifts.add(self)
        # If shift is no longer in a timesheet, remove it
        for ts in self.timesheet_set.all():
            if not self.processed:
                ts.shifts.remove(self)
            elif self.override_pay_period and ts.pay_period != self.override_pay_period:
                ts.shifts.remove(self)
            elif self.override_pay_period is None and pay_period != ts.pay_period:
                ts.shifts.remove(self)
            
            ts.check_empty()

    def delete(self, *args, **kwargs):
        # Validation: Cannot delete shift if it is processed
        if self.processed:
            raise ValidationError("Cannot delete this shift since it is processed. Please contact the Financial Director.")
        
        for ts in self.timesheet_set.all():
            ts.shifts.remove(self)
            
            ts.check_empty()
        super().delete(*args, **kwargs)

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
    shifts = models.ManyToManyField("Shift", blank=True)
    payments = models.ManyToManyField("EmployeePayment", blank=True)
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
                f"<a href='{reverse('finance:timesheet', args=[self.pk])}'>Get Timesheet: {self.employee}</a>"
                f"</div><br>"
            )
        )
    
    def get_admin_url(self):
        return reverse(
            "admin:%s_%s_change" % (self._meta.app_label, self._meta.model_name),
            args=(self.id,),
        )
    
    def cost(self):
        return (round(self.shifts.aggregate(Sum('cost'))['cost__sum'], 2) if self.shifts.count() > 0 else 0) + (round(self.payments.aggregate(Sum('amount'))['amount__sum'], 2) if self.payments.count() > 0 else 0)
    
    def check_empty(self):
        if self.shifts.count() == 0 and self.payments.count() == 0:
            self.delete()

    def save(self, *args, **kwargs):
        if self.paid_during is None:
            self.paid_during = self.pay_period
        super().save(*args, **kwargs)

        # Add timesheets to appropriate pay periods
        self.payperiod_set.clear()
        self.pay_period.timesheets.add(self)
        self.timesheets_paid_out.clear()
        self.paid_during.timesheets_paid_out.add(self)

        # Make sure all shifts are associated with this timesheet are saved to it
        emp_shifts = Shift.objects.filter(
            (
                Q(office_hours__employee=self.employee)
                |
                Q(job__employee=self.employee)
                |
                Q(trainee__employee=self.employee)
            )
            &
            Q(processed=True)
        )
        shifts = emp_shifts.filter(override_pay_period=self.pay_period)
        shifts = shifts | emp_shifts.filter(override_pay_period=None, time_in__gte=self.pay_period.start, time_in__lte=self.pay_period.end+timezone.timedelta(days=1))
        self.shifts.set(shifts)

        # Make sure all payments are associated with this timesheet are saved to it
        self.payments.set(EmployeePayment.objects.filter(
            Q(employee=self.employee)
            &
            (
                (
                    (
                        Q(date__gte=self.pay_period.start)
                        &
                        Q(date__lte=self.pay_period.end)
                    )
                    &
                    Q(override_pay_period=None)
                )
                |
                Q(override_pay_period=self.pay_period)
            )
        ))

        self.check_empty()

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
    timesheets = models.ManyToManyField("finance.TimeSheet")
    timesheets_paid_out = models.ManyToManyField("finance.TimeSheet", related_name="timesheets_paid_out") 

    def cost(self):
        total_cost = decimal.Decimal(0.00)
        for ts in self.timesheets.all():
            total_cost += ts.cost()
        return total_cost
    
    def outflow(self):
        total_cost = decimal.Decimal(0.00)
        for ts in self.timesheets_paid_out.exclude(signed=None):
            total_cost += ts.cost()
        return total_cost

    def get_summary(self):
        return format_html(
            f"<div style='margin: .25rem 0 .25rem 0'><a href='{reverse('finance:summary', args=[self.pk])}?time={datetime.now()}'>Print Summary</a><br><a href='{reverse('finance:summary_csv', args=[self.pk])}?time={datetime.now()}'>Summary CSV File</a></div><br>"
        )  # noqa

    def get_paychex_summary(self):
        tms = self.timesheets_paid_out.filter(employee__paychex_flex_workerID=None).exclude(signed=None).order_by('employee__last_name')
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

    def timesheets_for_this_pay_period(self):
        timesheets = self.timesheets_paid_out.order_by('employee__last_name')
        return format_html(
            "".join(
                [
                    (
                        f"<div style='margin: .25rem 0 .25rem 0'>"
                        f"<a href='{reverse('finance:timesheet', args=[timesheet.pk])}'>Get Timesheet: {timesheet.employee} {'<b>- SIGNED</b>' if timesheet.signed else ''}{(' - ('+str(timesheet.pay_period)+')') if timesheet.pay_period.pk is not self.pk else ''}</a>"
                        f"</div><br>"
                    )
                    for timesheet in timesheets
                ]
            )
        )

    def save(self):
        super().save()

        # Find shifts the fall within this pay period but are not associated with a timesheet
        unclaimed_shifts = Shift.objects.annotate(timesheet_count=Count("timesheet")).filter(timesheet_count=0, processed=True, time_in__gte=self.start, time_in__lte=self.end+timezone.timedelta(days=1))
        for shift in unclaimed_shifts:
            shift.save()

        # Find all payments that fall within this pay period but are not associated with a timesheet
        unclaimed_payments = EmployeePayment.objects.annotate(timesheet_count=Count("timesheet")).filter(timesheet_count=0, date__gte=self.start, date__lte=self.end)
        for payment in unclaimed_payments:
            payment.save()

        # Save all timesheets, in case the dates changed on the pay period        
        for timesheet in self.timesheets.all():
            timesheet.save()

        # When submitted. Take all unsubmitted timesheets and submit them with latest date
        if self.submitted:
            self.timesheets_paid_out.filter(processed=None).exclude(
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


class Transaction(models.Model):
    """
    Base transaction class
    """
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    outbound = models.BooleanField()
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=512)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class EmployeePayment(Transaction):
    """
    A one time payment made to an employee
    """
    employee = models.ForeignKey("employee.Employee", on_delete=models.CASCADE)
    override_pay_period = models.ForeignKey("PayPeriod", on_delete=models.CASCADE, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.outbound = True
        super().save(*args, **kwargs)

        pay_period = PayPeriod.objects.filter(start__lte=self.date, end__gte=self.date).first()
        if self.override_pay_period:
            tm, created = TimeSheet.objects.get_or_create(employee=self.employee, pay_period=self.override_pay_period)
            tm.payments.add(self)
        else:
            if pay_period:
                tm, created = TimeSheet.objects.get_or_create(employee=self.employee, pay_period=pay_period)
                tm.payments.add(self)
        # If shift is no longer in a timesheet, remove it
        for ts in self.timesheet_set.all():
            if self.override_pay_period and ts.pay_period != self.override_pay_period:
                ts.payments.remove(self)
            elif self.override_pay_period is None and pay_period != ts.pay_period:
                ts.payments.remove(self)

            ts.check_empty()

    def delete(self, *args, **kwargs):
        for ts in self.timesheet_set.all():
            ts.shifts.remove(self)

            ts.check_empty()
        super().delete(*args, **kwargs)

    def get_admin_url(self):
        return reverse(
            "admin:%s_%s_change" % (self._meta.app_label, self._meta.model_name),
            args=(self.id,),
        )

    def __str__(self):
        return f"{self.employee} - ${self.amount} - {self.date}"
