from django.contrib import admin
from finance.models import Payment, Wage, Shift, Estimate, Fee, OneTimeFee, PayPeriod
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

    inlines = [OneTimeFeeInline, PaymentInlineAdmin]
    list_display = ("__str__", "gig__start", "get_printout_link")
    list_filter = ('gig__start', 'gig__org')
    ordering = ['-gig__start']
    filter_horizontal = ["fees"]
    autocomplete_fields = ["gig", "billing_contact"]
    readonly_fields = ["subtotal", "fees_amt", "total_amt", "outstanding_balance", "get_printout_link"]
    fieldsets = (
        (
            "Information",
            {
                "fields": [
                    "status",
                    "gig",
                    "billing_contact",
                    "signed_estimate",
                    "notes",
                    "get_printout_link",
                ]
            },
        ),
        ("Billing info", {"fields": ["payment_due", "paid", "fees", "adjustments"]}),
        ("Bill", {"fields": ["subtotal", "fees_amt", "total_amt", "outstanding_balance"]}),
    )


@admin.register(PayPeriod)
class PayPeriodAdmin(admin.ModelAdmin):
    readonly_fields = ["get_summary", "associated_employees", "associated_shifts"]
    exclude = ["shifts"]
    search_fields = ["start", "end", "payday"]
