from django.contrib import admin, messages
from django.utils.html import format_html
from finance.models import (
    Payment,
    Wage,
    Shift,
    Estimate,
    Fee,
    OneTimeFee,
    PayPeriod,
    CannedNote,
)
from nested_admin import NestedGenericTabularInline
from djangoql.admin import DjangoQLSearchMixin



# Register your models here.
@admin.register(Wage)
class WageAdmin(admin.ModelAdmin):
    pass


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    autocomplete_fields = ["override_pay_period"]
    readonly_fields = ["total_time", "cost"]
    exclude = ["content_type", "content_object", "object_id"]
    list_filter = ("processed", "contested")
    pass


class ShiftInlineAdmin(NestedGenericTabularInline):
    readonly_fields = ["total_time", "cost"]
    exclude = ["paid_at"]
    model = Shift
    extra = 0


class OneTimeFeeInline(admin.StackedInline):
    model = OneTimeFee
    extra = 0


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    ordering = ['ordering']
    pass


class PaymentInlineAdmin(admin.StackedInline):
    model = Payment
    exclude = []
    extra = 0


@admin.register(Estimate)
class EstimateAdmin(DjangoQLSearchMixin, admin.ModelAdmin):

    @admin.action(description='Mark selected estimates as Show Concluded')
    def make_concluded(modeladmin, request, queryset):
        queryset.update(status='O')
        messages.add_message(
            request, messages.SUCCESS, "Estimates marked as concluded 👍"
        )

    @admin.action(description='Mark selected estimates as Awaiting Payment')
    def make_awaiting_payment(modeladmin, request, queryset):
        queryset.update(status='A')
        messages.add_message(
            request, messages.SUCCESS, "Estimates awaiting payment 👍"
        )
    
    @admin.action(description='Mark selected estimates as Closed')
    def make_closed(modeladmin, request, queryset):
        queryset.update(status='C')
        messages.add_message(
            request, messages.SUCCESS, "Estimates closed 👍"
        )

    @admin.action(description='Mark selected estimates as Abandoned')
    def make_abandoned(modeladmin, request, queryset):
        queryset.update(status='N')
        messages.add_message(
            request, messages.SUCCESS, "Estimates abandoned 👍"
        )

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
    def gig__day_of_show_notes(obj):
        return obj.gig.day_of_show_notes

    actions = [make_concluded, make_awaiting_payment, make_closed, make_abandoned]
    inlines = [OneTimeFeeInline, PaymentInlineAdmin]
    list_display = ("__str__", "gig__start", "get_printout_link")
    list_filter = (
        "status",
        "gig__start",
        "gig__org",
    )
    ordering = ["-gig__start"]
    filter_horizontal = ["fees", "canned_notes"]
    autocomplete_fields = ["gig", "billing_contact"]
    search_fields = (
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
        "gig__notes",
        "gig__day_of_show_notes",
    ]
    fieldsets = (
        (
            "Information",
            {
                "fields": [
                    "status",
                    "gig",
                    "billing_contact",
                    "signed_estimate",
                    "gig__notes",
                    "canned_notes",
                    "notes",
                    "get_printout_link",
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
                    "fees",
                    "adjustments",
                ]
            },
        ),
        (
            "Bill",
            {"fields": ["subtotal", "fees_amt", "total_amt", "outstanding_balance"]},
        ),
    )
    djangoql_completion_enabled_by_default = False


@admin.register(PayPeriod)
class PayPeriodAdmin(admin.ModelAdmin):
    readonly_fields = ["get_summary", "associated_employees", "associated_shifts"]
    exclude = ["shifts"]
    search_fields = ["start", "end", "payday"]


@admin.register(CannedNote)
class CannedNoteAdmin(admin.ModelAdmin):
    ordering = ["ordering"]
    search_fields = ["name", "note"]
