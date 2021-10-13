from django.urls.base import reverse
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.views import View
from django.core.mail import EmailMessage
from django.template.loader import get_template
import django.utils.timezone as timezone
from django.conf import settings
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib.auth.models import Group
from django.db.models import Sum
from django.core.exceptions import PermissionDenied
from employee.forms import (
    massAssignPaperworkForm,
    addGroupsForm,
    userCreationForm,
    userChangeForm,
    changePasswordForm,
    uploadForm,
)
from dev_utils.views import MultipleFormView
from SLUGS.views import SLUGSMixin, isAdminMixin
from utils.models import onboardingStatus
from finance.utils import getShiftsForEmployee
from finance.forms import ShiftFormSet
from finance.models import Shift
from employee.models import OfficeHours, PaperworkForm


# Create your views here.
class userSignup(FormView):
    form_class = userCreationForm
    success_url = "/employee/onboard/success"
    template_name = "employee/signup.html"

    def dispatch(self, request, *args, **kwargs):
        signup = onboardingStatus.objects.first()
        if signup.is_open is not True:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        template = get_template("employee/components/signup_email.html")
        email_template = template.render({"user": form.instance})
        email = EmailMessage(
            subject="Thanks for signing up for SLUGS",
            body=email_template,
            from_email="bssl.slugs@binghamtonsa.org",
            to=[form.instance.email],
            reply_to=["bssl@binghamtonsa.org"],
        )
        email.content_subtype = "html"
        email.send()
        return super().form_valid(form)


class userSignupComplete(TemplateView):
    template_name = "employee/signup_complete.html"


class userOverview(SLUGSMixin, MultipleFormView):
    template_name = "employee/overview.html"
    form_classes = {"userChangeForm": {"form": userChangeForm}}

    def process_forms(self, form_instances):
        for form in form_instances["forms"]:
            form_instances["forms"][form].save()
        messages.add_message(
            self.request, messages.SUCCESS, "We've updated your information 👍"
        )
        return self.render_to_response(self.get_context_data())

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("%s?next=%s" % (reverse("login"), request.path))
        self.form_classes["userChangeForm"]["instance"] = request.user
        self.added_context["shifts"] = getShiftsForEmployee(request.user)
        self.added_context["timeworked"] = self.added_context["shifts"].aggregate(
            Sum("total_time")
        )
        self.added_context["processed_shifts"] = self.added_context["shifts"].filter(
            processed=True
        )[:100]
        self.added_context["amount_made"] = self.added_context[
            "processed_shifts"
        ].aggregate(Sum("cost"))
        self.added_context["unprocessed_shifts"] = self.added_context["shifts"].filter(
            processed=False, contested=False
        )
        self.added_context["contested_shifts"] = self.added_context["shifts"].filter(
            contested=True
        )
        return super().dispatch(request, *args, **kwargs)


class officeHours(SLUGSMixin, MultipleFormView):
    template_name = "employee/office_hours.html"
    form_classes = {"office_hours": {"form": ShiftFormSet}}

    def dispatch(self, request, *args, **kwargs):
        if Group.objects.get(name="Manager") not in request.user.groups.all():
            raise PermissionDenied()
        office_hour_obj = OfficeHours.objects.get_or_create(employee=request.user)[0]
        self.form_classes["office_hours"]["kwargs"] = {
            "queryset": Shift.objects.filter(
                object_id=office_hour_obj.id,
                content_type_id=ContentType.objects.get(model="officehours").id,
                processed=False,
            )
        }
        return super().dispatch(request, *args, **kwargs)

    def process_forms(self, form_instances):
        office_hour_obj = OfficeHours.objects.get_or_create(employee=self.request.user)[
            0
        ]
        for form in form_instances["forms"]:
            for shift in form_instances["forms"][form].forms:
                if (
                    shift.instance.time_in is not None
                    and shift.instance.time_out is not None
                ):
                    shift.instance.object_id = office_hour_obj.id
                    shift.instance.content_type_id = ContentType.objects.get(
                        model="officehours"
                    ).id
                    shift.save()
            form_instances["forms"][form].save()
        messages.add_message(self.request, messages.SUCCESS, "Office Hours updated")
        return self.render_to_response(self.get_context_data())


class changePassword(SLUGSMixin, FormView):
    form_class = changePasswordForm
    template_name = "employee/change_password.html"
    success_url = reverse_lazy("employee:overview")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.add_message(
            self.request, messages.SUCCESS, "Password successfully updated"
        )
        return super().form_valid(form)


class uploadForm(SLUGSMixin, FormView):
    form_class = uploadForm
    template_name = "employee/upload_form.html"
    success_url = reverse_lazy("employee:overview")
    form_id = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.form_id
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        if request.user.pk is not None:
            self.form_id = PaperworkForm.objects.get(pk=kwargs["form_id"])
            if self.form_id.employee.pk != request.user.pk:
                raise PermissionDenied()
            self.added_context["paperwork"] = self.form_id
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.uploaded = timezone.now()
        form.save()
        messages.add_message(
            self.request, messages.SUCCESS, f"{form.instance.form} uploaded"
        )
        return super().form_valid(form)


class FormDownload(SLUGSMixin, View):
    def get(self, request, relative_path):
        path = f"forms/{relative_path}"
        absolute_path = "{}/{}".format(settings.MEDIA_ROOT, path)
        response = FileResponse(open(absolute_path, "rb"), as_attachment=True)
        return response


class FilledFormDownload(SLUGSMixin, View):
    def get(self, request, u_pk, relative_path):
        path = f"uploads/{u_pk}/{relative_path}"
        document = get_object_or_404(PaperworkForm, pdf=path)
        if request.user.is_staff or document.employee.pk == request.user.pk:
            absolute_path = "{}/{}".format(settings.MEDIA_ROOT, path)
            response = FileResponse(open(absolute_path, "rb"), as_attachment=True)
            return response
        else:
            raise PermissionDenied()


class massAssignPaperwork(SLUGSMixin, FormView):
    form_class = massAssignPaperworkForm
    template_name = "employee/mass_assign_paperwork.html"
    success_url = reverse_lazy("admin:employee_employee_changelist")

    def dispatch(self, request, *args, **kwargs):
        self.initial["ids"] = kwargs["selected"]
        self.added_context["selected_ids"] = kwargs["selected"]
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.add_forms(self.request)
        messages.add_message(
            self.request, messages.SUCCESS, f"Forms assigned and emails sent"
        )
        return super().form_valid(form)

class addGroups(SLUGSMixin, isAdminMixin, FormView):
    form_class = addGroupsForm
    template_name = "employee/add_groups.html"
    success_url = reverse_lazy("admin:employee_employee_changelist")

    def dispatch(self, request, *args, **kwargs):
        self.initial["ids"] = kwargs["selected"]
        self.added_context["selected_ids"] = kwargs["selected"]
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.add_groups(self.request)
        messages.add_message(
            self.request, messages.SUCCESS, f"Groups added"
        )
        return super().form_valid(form)
