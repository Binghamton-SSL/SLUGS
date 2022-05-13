from django.contrib import admin
from django.urls import path
from django.contrib.contenttypes.models import ContentType
from nested_admin import NestedStackedInline, NestedModelAdmin, NestedTabularInline
from fieldsets_with_inlines import FieldsetsInlineMixin
from gig.forms import GigJobChangeForm, GigSystemsChangeForm, GigLoadinChangeForm
from .models import SystemInstance, Gig, Job, LoadIn, JobInterest, AddonInstance
from .views import staffShow, SendStaffingEmail
from finance.admin import ShiftInlineAdmin
from djangoql.admin import DjangoQLSearchMixin


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


@admin.register(Gig)
class GigAdmin(DjangoQLSearchMixin, FieldsetsInlineMixin, NestedModelAdmin):
    djangoql_completion_enabled_by_default = False
    search_fields = ["name", "org__name", "contact__name", "location__name"]
    inlines = (LoadInInline, SystemInline)
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
        ("Day of Show Info", {"fields": ("day_of_show_notes",)}),
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

    def save_formset(self, request, form, formset, change):
        for form in formset.forms:
            form.save()
            if hasattr(form, "nested_formsets"):
                for job_form in form.nested_formsets:
                    for job in job_form:
                        job.instance.gig = form.instance.gig
                        job.save()
                        if hasattr(job, "nested_formsets"):
                            for shift_form in job.nested_formsets:
                                for shift in shift_form:
                                    shift.instance.object_id = job.instance.id
                                    shift.instance.content_type_id = (
                                        ContentType.objects.get(model="job").id
                                    )
                                    shift.save()
        super(GigAdmin, self).save_formset(request, form, formset, change)

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
    pass
