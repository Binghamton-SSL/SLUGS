from django.contrib import admin
from django.urls import path
from django.contrib.contenttypes.models import ContentType
from nested_admin import NestedStackedInline, NestedModelAdmin, NestedTabularInline
from fieldsets_with_inlines import FieldsetsInlineMixin
from gig.forms import GigJobChangeForm, GigSystemsChangeForm, GigLoadinChangeForm
from .models import SystemInstance, Gig, Job, LoadIn, JobInterest, AddonInstance, BingoBoard, BingoTile, TileOnBoard, SubcontractedEquipment, SubcontractedEquipmentInstance
from .views import staffShow, SendStaffingEmail
from finance.admin import ShiftInlineAdmin, VendorFeeInline
from djangoql.admin import DjangoQLSearchMixin
from utils.admin import AttachmentInlineAdmin


class JobSubInline(NestedTabularInline):
    formset = GigJobChangeForm
    inlines = (ShiftInlineAdmin,)
    autocomplete_fields = ["employee", "position"]
    model = Job
    exclude = ["gig"]
    extra = 0


class JobInline(NestedTabularInline):
    inlines = (ShiftInlineAdmin,)
    autocomplete_fields = ["employee", "position"]
    model = Job
    exclude = ["linked_system"]
    extra = 0


class AddonInline(NestedTabularInline):
    autocomplete_fields = ["addon"]
    model = AddonInstance
    extra = 0


class SystemInline(NestedStackedInline):
    formset = GigSystemsChangeForm
    autocomplete_fields = ["system"]
    model = SystemInstance
    inlines = (JobSubInline, AddonInline)
    extra = 0


class LoadInInline(NestedTabularInline):
    formset = GigLoadinChangeForm
    model = LoadIn
    extra = 0


class SubcontractedEquipmentInstanceInline(NestedTabularInline):
    verbose_name = "Rented Equipment"
    verbose_name_plural = "Rented Equipment"
    model = SubcontractedEquipmentInstance
    extra = 0
    autocomplete_fields = ["equipment"]


class SubcontractedEquipmentInline(NestedStackedInline):
    model = SubcontractedEquipment
    exclude = ["fees"]
    readonly_fields = ["get_printout_link"]
    autocomplete_fields = ["vendor"]
    inlines = [SubcontractedEquipmentInstanceInline, VendorFeeInline]
    extra = 0


@admin.register(Gig)
class GigAdmin(DjangoQLSearchMixin, FieldsetsInlineMixin, NestedModelAdmin):
    djangoql_completion_enabled_by_default = False
    search_fields = ["name", "org__name", "contact__name", "location__name"]
    inlines = (LoadInInline, SystemInline, SubcontractedEquipmentInline, AttachmentInlineAdmin)
    autocomplete_fields = ["org", "contact", "location"]
    list_display = (
        "__str__",
        "get_staff_link",
        "send_staffing_email",
    )
    list_filter = ["systems", "org", "location"]
    ordering = ["-start"]
    readonly_fields = ["day_of_show_notes", "get_staff_link", "send_staffing_email"]
    fieldsets_with_inlines = [
        (
            "Event Information",
            {
                "fields": (
                    "name",
                    "setup_by",
                    "start",
                    "end",
                    "org",
                    "contact",
                    "location",
                    "notes",
                    "get_staff_link",
                    "send_staffing_email",
                )
            },
        ),
        LoadInInline,
        SystemInline,
        SubcontractedEquipmentInline,
        ("Day of Show Info", {"fields": ("day_of_show_notes",)}),
        AttachmentInlineAdmin,
        (
            None,
            {
                "fields": (
                    "archived",
                    "published",
                    "available_for_signup",
                    "manager_only_notes",
                )
            },
        ),
    ]

    def save_related(self, request, form, formset, change):
        for fset in formset:
            if fset.form.Meta.model == Job:
                for job in fset.forms:
                    job.instance.gig_id = form.instance.pk
                    job.instance.save()
            else:
                fset.save()
        super(GigAdmin, self).save_related(request, form, formset, change)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path("<path:object_id>/staff/", staffShow.as_view(), name="gig_gig_staff"),
            path(
                "<path:object_id>/sendEmail/",
                SendStaffingEmail.as_view(),
                name="gig_gig_email",
            ),
        ]
        return my_urls + urls


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    search_fields = ["employee__first_name", "employee__last_name", "gig__name"]
    list_display = ["__str__", "employee"]
    pass


@admin.register(JobInterest)
class JobInterestAdmin(DjangoQLSearchMixin ,admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    search_fields = ["employee__first_name", "employee__last_name"]


class TileOnBoardInline(admin.StackedInline):
    model = TileOnBoard
    extra = 0


@admin.register(BingoBoard)
class BingoBoardAdmin(admin.ModelAdmin):
    inlines = [TileOnBoardInline]


@admin.register(BingoTile)
class BingoTileAdmin(admin.ModelAdmin):
    pass

@admin.register(SubcontractedEquipment)
class SubcontractedEquipmentAdmin(NestedModelAdmin):
    exclude = ["equipment", "fees"]
    readonly_fields = ["get_printout_link"]
    autocomplete_fields = ["gig", "vendor"]
    inlines = [SubcontractedEquipmentInstanceInline, VendorFeeInline]
