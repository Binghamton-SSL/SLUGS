from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.template.loader import get_template
from django.http import HttpResponseRedirect
from django.urls.base import reverse
from import_export import resources
from import_export.admin import ImportExportMixin
from finance.admin import ShiftInlineAdmin
from employee.models import PaperworkForm, Paperwork
from utils.generic_email import send_generic_email
from djangoql.admin import DjangoQLSearchMixin
from django.conf import settings


from .models import Employee, OfficeHours


class PaperworkInline(admin.StackedInline):
    model = PaperworkForm
    autocomplete_fields = ["form"]
    exclude = []
    extra = 0
    readonly_fields = ["uploaded", "requested"]

class PaperworkInlineWOOldEmployees(admin.StackedInline):
    model = PaperworkForm
    autocomplete_fields = ["form"]
    exclude = []
    extra = 0
    readonly_fields = ["uploaded", "requested"]

    def get_queryset(self, request):
        qs = super(PaperworkInlineWOOldEmployees, self).get_queryset(request)
        return qs.filter(employee__is_active=True)




@admin.register(Paperwork)
class PaperworkAdmin(admin.ModelAdmin):
    search_fields = ["form_name"]
    readonly_fields = ["associated_forms"]
    inlines = [PaperworkInlineWOOldEmployees]
    ordering = ["-edited"]
    pass


class EmployeeResource(resources.ModelResource):
    class Meta:
        model = Employee
        fields = (
            "id",
            "email",
            "preferred_name",
            "first_name",
            "last_name",
            "bnum",
            "phone_number",
            "is_grad_student",
            "graduation_year",
            "final_year_with_bssl",
            "last_login",
            "date_joined",
            "end_of_employment",
            "is_active",
            "is_staff",
            "is_superuser",
        )


@admin.register(Employee)
class EmployeeAdmin(DjangoQLSearchMixin, ImportExportMixin, UserAdmin):
    resource_class = EmployeeResource

    def group(self, user):
        groups = []
        for group in user.groups.all():
            groups.append(group.name)
        return ", ".join(groups)

    def signature_on_file(self, user):
        if user.signature:
            return "Signature Stored"
        else:
            return "No Signature"

    def save_model(self, request, obj, form, change):
        if "is_active" in form.changed_data and form.instance.is_active:
            send_generic_email(
                request=request,
                title="Your SLUGS account has been activated",
                included_text=f"""
Hey there {(form.instance.preferred_name if form.instance.preferred_name else form.instance.first_name)},
<br><br>
Got some good news for ya, Your SLUGS account has been activated. Feel free to <a href="https://slugs.bssl.binghamtonsa.org/">head over to SLUGS</a> and take a peek around.
""",  # noqa
                subject=f"SLUGS account activation - {form.instance.email}",
                to=[form.instance.email],
            )
            if form.instance.paperworkform_set.filter(processed=False).count() != 0:
                forms = form.instance.paperworkform_set.filter(processed=False).all()
                attachments = [f.form.form_pdf.file.name for f in forms]
                template = get_template("employee/components/general_forms.html")
                email_template = template.render({"request": request})
                send_generic_email(
                    request=request,
                    subject="[ACTION REQUIRED] New forms to fill out on SLUGS",
                    title=f"Paperwork needed: {', '.join([f.form.form_name for f in forms])}",
                    included_html=email_template,
                    included_text=f"How's it going {(form.instance.preferred_name if form.instance.preferred_name else form.instance.first_name)}, <br><br> Attached (and on SLUGS) you'll find a/some new form(s) we need you to fill out. You can upload it to SLUGS by clicking the button above or by going to the 'You' tab in SLUGS and clicking on the appropriate document under the 'Paperwork' section.<br><br>Thanks!<br>",  # noqa
                    to=[form.instance.email],
                    attachments=attachments,
                )
        elif "is_active" in form.changed_data and not form.instance.is_active:
            send_generic_email(
                request=request,
                title="Your SLUGS account has been deactivated",
                included_text=f"""
Hey there {(form.instance.preferred_name if form.instance.preferred_name else form.instance.first_name)},
<br><br>
We're sorry to see ya go. One of our managers has deactivated your account. If you believe this was done in error please <a href="mailto:{settings.BSSL_EMAIL_ADDRESS}">reach out</a>.
""",  # noqa
                subject=f"SLUGS account deactivation - {form.instance.email}",
                to=[form.instance.email],
            )
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        if change is True:
            for form in formset.forms:
                if "form" in form.changed_data and form.instance.pdf.name is None:
                    form.save()
                    attachments = [form.instance.form.form_pdf.file.name]
                    template = get_template("employee/components/form.html")
                    email_template = template.render(
                        {"form": form.instance, "request": request}
                    )
                    send_generic_email(
                        request=request,
                        subject=f"[ACTION REQUIRED] Fill out '{form.instance.form.form_name}' on SLUGS",
                        title=f"Paperwork needed: {form.instance.form.form_name}",
                        included_html=email_template,
                        included_text=f"How's it going {(form.instance.preferred_name if form.instance.preferred_name else form.instance.first_name)}, <br><br> Attached (and on SLUGS) you'll find a new form we need you to fill out. You can upload it to SLUGS by clicking the button above or by going to the 'You' tab in SLUGS and click on the appropriate document.<br><br>Thanks!<br>",  # noqa
                        to=[form.instance.employee.email],
                        attachments=attachments,
                    )
        super().save_formset(request, form, formset, change)

    @admin.action(description="Assign Paperwork")
    def mass_assign_paperwork(modeladmin, request, queryset):
        selected = queryset.values_list("pk", flat=True)
        return HttpResponseRedirect(
            "/employee/mass-assign-paperwork/%s"
            % (",".join(str(pk) for pk in selected),)
        )
        return reverse("employee:mass_assign", args=[queryset])

    @admin.action(description="Add Groups")
    def add_groups(modeladmin, request, queryset):
        selected = queryset.values_list("pk", flat=True)
        return HttpResponseRedirect(
            "/employee/add-groups/%s" % (",".join(str(pk) for pk in selected),)
        )
        return reverse("employee:add_groups", args=[queryset])

    group.short_description = "Groups"

    list_display = (
        "__str__",
        "group",
        "is_active",
        "is_staff",
        "is_superuser",
        "paperwork_outstanding",
    )
    list_filter = ("is_active", "is_staff", "is_superuser", "groups", "graduation_year")
    actions = [mass_assign_paperwork, add_groups]
    readonly_fields = ["last_login", "signature_on_file", "employee_metrics"]

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets

        if request.user.is_superuser:
            perm_fields = (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        else:
            perm_fields = ("is_active", "is_staff", "groups")

        return [
            (None, {"fields": ("email", "password", "last_login", "date_joined", "end_of_employment")}),
            (
                "Personal info",
                {
                    "fields": (
                        "preferred_name",
                        "first_name",
                        "last_name",
                        "phone_number",
                        "bnum",
                        "id_barcode",
                        "graduation_year",
                        "is_grad_student",
                        "final_year_with_bssl",
                        "signature_on_file",
                        "employee_notes",
                    )
                },
            ),
            ("Employee Metrics", {"fields": ["employee_metrics"]}),
            ("Permissions", {"fields": perm_fields}),
        ]

    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "preferred_name",
                    "first_name",
                    "last_name",
                    "bnum",
                    "graduation_year",
                    "is_grad_student",
                    "final_year_with_bssl",
                ),
            },
        ),
    )
    search_fields = (
        "email",
        "preferred_name",
        "first_name",
        "last_name",
        "bnum",
        "graduation_year",
        "final_year_with_bssl",
        "phone_number",
        "groups__name",
    )
    djangoql_completion_enabled_by_default = False
    ordering = (
        "-is_active",
        "last_name",
        "email",
    )
    inlines = [PaperworkInline]
    filter_horizontal = (
        "groups",
        "user_permissions",
    )


@admin.register(OfficeHours)
class OfficeHoursAdmin(admin.ModelAdmin):
    inlines = [ShiftInlineAdmin]
    list_display = ["employee", "position"]

@admin.register(PaperworkForm)
class PaperworkFormAdmin(admin.ModelAdmin):
    pass