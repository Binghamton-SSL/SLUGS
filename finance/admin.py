from django.contrib import admin
from django.utils.html import format_html
from finance.models import Payment, Wage, Shift, Estimate, Fee, OneTimeFee, PayPeriod, CannedNote
from nested_admin import NestedGenericTabularInline


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
    pass


class PaymentInlineAdmin(admin.StackedInline):
    model = Payment
    exclude = []
    extra = 0


@admin.register(Estimate)
class EstimateAdmin(admin.ModelAdmin):
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
        ("Billing info", {"fields": ["payment_due", "paid", "fees", "adjustments"]}),
        (
            "Bill",
            {"fields": ["subtotal", "fees_amt", "total_amt", "outstanding_balance"]},
        ),
    )


@admin.register(PayPeriod)
class PayPeriodAdmin(admin.ModelAdmin):
    readonly_fields = ["get_summary", "associated_employees", "associated_shifts"]
    exclude = ["shifts"]
    search_fields = ["start", "end", "payday"]


@admin.register(CannedNote)
class CannedNoteAdmin(admin.ModelAdmin):
    ordering = ["ordering"]
    search_fields = ["name", "note"]