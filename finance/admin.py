from django.contrib import admin, messages
from django.utils.html import format_html
import django.utils.timezone as timezone
from SLUGS.templatetags.grouping import has_group
from finance.forms import PricingChangeForm, ShiftChangeForm, HourlyRateChangeForm
from finance.models import (
    EmployeePayment,
    FeePricing,
    HourlyRate,
    Payment,
    SystemAddonPricing,
    SystemPricing,
    VendorEquipmentPricing,
    TimeSheet,
    Wage,
    Shift,
    Estimate,
    Fee,
    VendorFee,
    OneTimeFee,
    PayPeriod,
    CannedNote,
)
from nested_admin import NestedGenericTabularInline, NestedTabularInline
from djangoql.admin import DjangoQLSearchMixin
from adminsortable2.admin import SortableInlineAdminMixin


class HourlyRateInline(admin.StackedInline):
    model = HourlyRate
    formset = HourlyRateChangeForm
    extra = 0


class SystemPricingInline(admin.StackedInline):
    formset = PricingChangeForm
    model = SystemPricing
    extra = 0


class FeePricingInline(admin.StackedInline):
    formset = PricingChangeForm
    model = FeePricing
    extra = 0


class SystemAddonPricingInline(admin.StackedInline):
    formset = PricingChangeForm
    model = SystemAddonPricing
    extra = 0


class VendorEquipmentPricingInline(admin.StackedInline):
    formset = PricingChangeForm
    model = VendorEquipmentPricing
    extra = 0


class VendorFeeInline(NestedTabularInline):
    model = VendorFee
    extra = 0

@admin.register(Wage)
class WageAdmin(admin.ModelAdmin):
    inlines = [HourlyRateInline]


@admin.register(Shift)
class ShiftAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    autocomplete_fields = ["override_pay_period"]
    exclude = ["content_type", "content_object", "object_id"]
    list_filter = ("processed", "contested")
    search_fields = ["job__employee__first_name",
                     "job__employee__last_name",
                     "job__gig__name",
                     "office_hours__employee__first_name",
                     "office_hours__employee__last_name",
                     "trainee__employee__first_name",
                     "trainee__employee__last_name",
                     "time_in",
                     "time_out",
                     "description"]
    djangoql_completion_enabled_by_default = False
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.processed:
            return ["time_in",
                    "time_out", 
                    "description",
                    "contested",
                    "reason_contested",
                    "total_time",
                    "cost",
                    "paid_at"]
        else:
            return ["total_time", "cost", "paid_at"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if obj:
            return not obj.processed

    def get_fieldsets(self, request, obj=None):
        base_fieldsets = [
            ("Shift Details",
                {
                    "fields": [
                        "time_in",
                        "time_out",
                        "description",
                    ] + (["total_time"] if obj else [])
                })
        ] + ([
            ("Financial Details",
                {
                    "fields": [
                        "processed",
                        "contested",
                        "reason_contested",
                        "override_pay_period",
                    ] + (["paid_at", "cost"] if obj else [])
                })
        ] if (has_group(request.user, "Financial Director/GM") or has_group(request.user, "SA Employee") or request.user.is_superuser) else [
            ("Financial Details",
                {
                    "fields": (["paid_at", "cost"] if obj else [])
                })
        ])
        return base_fieldsets


class ShiftInlineAdmin(NestedGenericTabularInline):
    readonly_fields = ["total_time", "cost", "paid_at"]
    model = Shift
    extra = 0

    formset = ShiftChangeForm

    def get_fieldsets(self, request, obj=None):
        base_fieldsets = [
            ("Shift Details",
                {
                    "fields": ([
                        "time_in",
                        "time_out",
                        "description",
                    ] + (["total_time"] if obj else [])) +
                    (([
                        "processed",
                        "contested",
                        "reason_contested",
                        "override_pay_period",
                    ] + (["paid_at", "cost"] if obj else [])) if (has_group(request.user, "Financial Director/GM") or has_group(request.user, "SA Employee") or request.user.is_superuser) else ["cost"])
                })
        ]
        return base_fieldsets


class OneTimeFeeInline(SortableInlineAdminMixin, admin.StackedInline):
    autocomplete_fields = ["prepared_fee"]
    model = OneTimeFee
    readonly_fields = ["or_create_your_own"]
    fields = [
        "prepared_fee",
        "or_create_your_own",
        "name",
        "amount",
        "percentage",
        "description",
    ]
    extra = 0


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    search_fields = ["name", "description"]
    inlines = [FeePricingInline]
    pass


class PaymentInlineAdmin(admin.StackedInline):
    model = Payment
    exclude = []
    extra = 0


@admin.register(Estimate)
class EstimateAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    @admin.action(description="Mark selected estimates as Show Concluded")
    def make_concluded(modeladmin, request, queryset):
        for estimate in queryset.all():
            estimate.status = "O"
            estimate.gig.archived = True
            estimate.gig.save()
            estimate.save()
        messages.add_message(
            request, messages.SUCCESS, "Estimates marked as concluded 👍"
        )

    @admin.action(description="Mark selected estimates as Awaiting Payment")
    def make_awaiting_payment(modeladmin, request, queryset):
        queryset.update(status="A")
        messages.add_message(request, messages.SUCCESS, "Estimates awaiting payment 👍")

    @admin.action(description="Mark selected estimates as Closed")
    def make_closed(modeladmin, request, queryset):
        queryset.update(status="C")
        messages.add_message(request, messages.SUCCESS, "Estimates closed 👍")

    @admin.action(description="Mark selected estimates as Abandoned")
    def make_abandoned(modeladmin, request, queryset):
        queryset.update(status="N")
        messages.add_message(request, messages.SUCCESS, "Estimates abandoned 👍")

    @staticmethod
    def gig__start(obj):
        return obj.gig.start

    @staticmethod
    def gig__org(obj):
        return obj.gig.org

    @staticmethod
    def gig__notes(obj):
        return (
            format_html(
                f"<b>This will show up on the estimate as 'ATTN ENG':</b>\n{obj.gig.notes}"
            )
            if obj.gig.notes
            else "No ATTN ENG for this gig"
        )

    @staticmethod
    def gig__manager_notes(obj):
        return (
            format_html(
                f"<b>This is information is for managers view only:</b>\n{obj.gig.manager_only_notes}"
            )
            if obj.gig.manager_only_notes
            else "No Manager Notes for this gig"
        )

    @staticmethod
    def gig__day_of_show_notes(obj):
        return obj.gig.day_of_show_notes

    @staticmethod
    def gig__outflow(obj):
        return obj.gig.calculate_outflow()

    @staticmethod
    def estimate_id(obj):
        return 2500 + int(obj.pk)

    @staticmethod
    def reservation_number(obj):
        return f"E{2500+int(obj.pk)}"

    @staticmethod
    def invoice_number(obj):
        return f"SA7400-I{2500+obj.pk}"

    @staticmethod
    def vendor_subcontracted_equipment_orders(obj):
        vendorset = obj.gig.subcontractedequipment_set.filter(client_provided=False)
        return "None" if vendorset.count() == 0 else format_html(f"""
        <div>
        {" ".join([vendorcontract.get_printout_link() for vendorcontract in vendorset.all()])}
        </div>
        """)

    actions = [make_concluded, make_awaiting_payment, make_closed, make_abandoned]
    inlines = [OneTimeFeeInline, PaymentInlineAdmin]
    list_display = ("__str__", "gig__start", "get_printout_link")
    list_filter = (
        "status",
        "gig__start",
        "gig__org",
    )
    ordering = ["-gig__start"]
    filter_horizontal = ["canned_notes"]
    autocomplete_fields = ["gig", "billing_contact"]
    search_fields = (
        "pk",
        "estimate_id",
        "gig__name",
        "gig__org__name",
        "gig__org__SA_account_num",
        "billing_contact__name",
    )
    readonly_fields = [
        "subtotal",
        "fees_amt",
        "total_amt",
        "outstanding_balance",
        "get_printout_link",
        "vendor_subcontracted_equipment_orders",
        "gig__notes",
        "gig__day_of_show_notes",
        "gig__manager_notes",
        "gig__outflow",
    ]
    exclude = ["estimate_id"]
    fieldsets = (
        (
            "Information",
            {
                "fields": [
                    "gig__manager_notes",
                    "status",
                    "gig",
                    "billing_contact",
                    "signed_estimate",
                    "gig__notes",
                    "canned_notes",
                    "notes",
                    "get_printout_link",
                    "vendor_subcontracted_equipment_orders",
                ]
            },
        ),
        (
            "Billing info",
            {
                "fields": [
                    "gig__day_of_show_notes",
                    "payment_due",
                    "paid",
                    "adjustments",
                ]
            },
        ),
        (
            "Bill",
            {"fields": ["subtotal", "fees_amt", "total_amt", "outstanding_balance", "gig__outflow"]},
        ),
    )
    djangoql_completion_enabled_by_default = False


@admin.register(TimeSheet)
class TimeSheetAdmin(admin.ModelAdmin):
    exclude = ["shifts"]
    readonly_fields = ["pay_period", "printout_link", "links_to_shifts", "links_to_payments", "employee"]
    search_fields = ["employee__first_name", "employee__last_name"]

    def has_add_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.processed:
            return ["pay_period",
                    "printout_link",
                    "links_to_shifts",
                    "links_to_payments",
                    "employee",
                    "signed",
                    "paid_during",
                    "available_to_auto_sign",
                    "pdf"] + (
                        # Timesheet is locked after 6 months
                        ["processed"] if (timezone.now() - timezone.timedelta(weeks=(4*6))).date() > obj.processed else []
                    )
        else:
            return ["pay_period", "printout_link", "links_to_shifts", "links_to_payments", "employee"] + (
                        # Timesheet signed is locked after 1 week
                        ["signed"] if (obj.signed and (timezone.now() - timezone.timedelta(weeks=3)) > obj.signed) else []
                    )

    def has_delete_permission(self, request, obj=None):
        return False

    def links_to_shifts(self, obj):
        ret = ""
        for shift in obj.shifts.all().order_by("time_in"):
            ret += f"<a href='{shift.get_admin_url()}'>{timezone.template_localtime(shift.time_in).strftime('%m/%d/%y %H:%M:%S')} - {timezone.template_localtime(shift.time_out).strftime('%m/%d/%y %H:%M:%S')} <b>{shift.content_object}</b> ({shift.total_time} - ${shift.cost}) </a><br>"
        return format_html(ret)
    
    def links_to_payments(self, obj):
        ret = ""
        for payment in obj.payments.all().order_by("date"):
            ret += f"<a href='{payment.get_admin_url()}'>{payment}</a><br>"
        return format_html(ret)

    def get_fieldsets(self, request, obj=None):
        return [
            (None, {
                "fields": [
                    "employee",
                    "pay_period",
                    "paid_during",
                    "signed",
                    "processed",
                    "available_to_auto_sign",
                    "pdf",
                    "printout_link",
                    "links_to_shifts",
                    "links_to_payments",
                ]
            })
        ]


class TimeSheetInline(admin.StackedInline):
    verbose_name = "Unlocked Time Sheet"
    verbose_name_plural = "Unlocked Time Sheets"
    model = TimeSheet
    readonly_fields = ["printout_link", "links_to_shifts", "links_to_payments", "employee"]
    exclude = ["shifts"]
    fk_name = "pay_period"
    extra = 0
    ordering = ("processed",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(processed=None)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
    def links_to_shifts(self, obj):
        ret = ""
        for shift in obj.shifts.all().order_by("time_in"):
            ret += f"<a href='{shift.get_admin_url()}'>{timezone.template_localtime(shift.time_in).strftime('%m/%d/%y %H:%M:%S')} - {timezone.template_localtime(shift.time_out).strftime('%m/%d/%y %H:%M:%S')} <b>{shift.content_object}</b> ({shift.total_time} - ${shift.cost}) </a><br>"
        return format_html(ret)
    
    def links_to_payments(self, obj):
        ret = ""
        for payment in obj.payments.all().order_by("date"):
            ret += f"<a href='{payment.get_admin_url()}'>{payment}</a><br>"
        return format_html(ret)
    
    def get_fieldsets(self, request, obj=None):
        return [
            (None, {
                "fields": [
                    "employee",
                    "pay_period",
                    "paid_during",
                    "signed",
                    "processed",
                    "available_to_auto_sign",
                    "pdf",
                    "printout_link",
                    "links_to_shifts",
                ]
            })
        ]


class SoonLockedTimeSheetInline(TimeSheetInline):
    verbose_name = "Soon to be Locked Time Sheet"
    verbose_name_plural = "Soon to be Locked Time Sheets"
    readonly_fields = ["printout_link",
                       "links_to_shifts",
                       "links_to_payments",
                       "employee",
                       "signed",
                       "pdf",
                       "paid_during",
                       "available_to_auto_sign"]

    def get_queryset(self, request):
        qs = self.model._default_manager.get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        qs = qs.exclude(processed__lte=(timezone.now() - timezone.timedelta(weeks=(4*6))))
        return qs.exclude(processed=None)


class LockedTimeSheetInline(TimeSheetInline):
    verbose_name = "Locked Time Sheet"
    verbose_name_plural = "Locked Time Sheets"

    def has_change_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = self.model._default_manager.get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        qs = qs.exclude(processed__gte=(timezone.now() - timezone.timedelta(weeks=(4*6))))
        return qs.exclude(processed=None)

@admin.register(PayPeriod)
class PayPeriodAdmin(admin.ModelAdmin):
    readonly_fields = ["cost", "outflow", "get_summary", "get_paychex_summary", "timesheets_for_this_pay_period"]
    exclude = ["timesheets", "timesheets_paid_out"]
    search_fields = ["start", "end", "payday"]
    list_display = ["payday", "start", "end", "submitted"]

    def get_inlines(self, request, obj=None):
        # Show the timesheet lifecycles that apply
        inlines = []
        if obj:
            if TimeSheet.objects.filter(pay_period=obj.pk, processed=None).count() > 0:
                inlines.append(TimeSheetInline)
            if TimeSheet.objects.filter(pay_period=obj.pk, processed__gte=(timezone.now() - timezone.timedelta(weeks=(4*6)))):
                inlines.append(SoonLockedTimeSheetInline)
            if TimeSheet.objects.filter(pay_period=obj.pk, processed__lte=(timezone.now() - timezone.timedelta(weeks=(4*6)))):
                inlines.append(LockedTimeSheetInline)
        return inlines
        # Default, show all
        # return [TimeSheetInline, SoonLockedTimeSheetInline, LockedTimeSheetInline]

    def get_form(self, request, obj=None, **kwargs):
        help_texts = {'timesheets_for_this_pay_period': 'All timesheets that are due to be PAID during this pay period. This includes timesheets not listed below since they were created during another pay period. Timesheets from another pay period will be post-marked with the timeframe of their original pay period'}
        kwargs.update({'help_texts': help_texts})
        return super(PayPeriodAdmin, self).get_form(request, obj, **kwargs)


@admin.register(CannedNote)
class CannedNoteAdmin(admin.ModelAdmin):
    ordering = ["ordering"]
    search_fields = ["name", "note"]


@admin.register(EmployeePayment)
class EmployeePaymentAdmin(admin.ModelAdmin):
    exclude = ["outbound"]
    search_fields = ["employee", "amount", "description"]
    autocomplete_fields = ["employee", "override_pay_period"]
    fields = ["employee", "date", "amount", "description", "override_pay_period"]
