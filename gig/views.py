from SLUGS.templatetags.grouping import has_group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from dev_utils.views import MultipleFormView
from django.views.generic.base import TemplateView
from SLUGS.views import SLUGSMixin
from gig.models import Gig, Job, JobInterest
from employee.models import Employee

from finance.forms import ShiftFormSet
from gig.forms import shiftFormHelper, engineerNotesForm, StaffShowForm
from finance.models import Shift
from utils.models import signupStatus


# Create your views here.
class gigIndex(SLUGSMixin, MultipleFormView):
    template_name = "gig/gig.html"
    form_classes = {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for form in context["forms"]:
            if form != "show_notes":
                if form in context["job_forms"]:
                    context["forms"][form] = {
                        "form": context["forms"][form],
                        "employee": context["job_forms"][form].employee,
                    }
        return context

    def dispatch(self, request, *args, **kwargs):
        self.form_classes = {
            "show_notes": {
                "form": engineerNotesForm,
            }
        }
        jobs = {}
        self.added_context["helper"] = shiftFormHelper()
        self.added_context["gig"] = Gig.objects.get(pk=kwargs["gig_id"])
        if not self.added_context["gig"].published:
            raise PermissionDenied()
        try:
            self.added_context["my_job"] = (
                Job.objects.get(employee=request.user, gig=self.added_context["gig"])
                if request.user.is_authenticated
                else ""
            )
        except Exception:
            self.added_context["my_job"] = False
        for job in self.added_context["gig"].job_set.all():
            jobs[f"job_form_{job.id}"] = job
            self.form_classes[f"job_form_{job.id}"] = {
                "form": ShiftFormSet,
                "kwargs": {
                    "queryset": Shift.objects.filter(
                        object_id=job.id,
                        content_type_id=ContentType.objects.get(model="job").id,
                    )
                },
            }
        self.form_classes["show_notes"]["instance"] = self.added_context["gig"]
        self.added_context["job_forms"] = jobs
        return super().dispatch(request, *args, **kwargs)

    def process_forms(self, form_instances):
        for form in form_instances["forms"]:
            if form == "show_notes":
                form_instances["forms"][form].save()
            else:
                for shift in form_instances["forms"][form].forms:
                    if "DELETE" in shift.changed_data:
                        shift.save()
                        continue
                    if (
                        shift.instance.time_in is not None
                        and shift.instance.time_out is not None
                    ):
                        shift.instance.object_id = self.added_context["job_forms"][
                            form
                        ].id
                        shift.instance.content_type_id = ContentType.objects.get(
                            model="job"
                        ).id
                        shift.save()
                form_instances["forms"][form].save()
        messages.add_message(self.request, messages.SUCCESS, "Day of Show updated")
        return self.render_to_response(self.get_context_data())


class workSignup(SLUGSMixin, TemplateView):
    template_name = "gig/signup.html"

    def dispatch(self, request, *args, **kwargs):
        if not signupStatus.objects.all().first().is_open or has_group(
            request.user, "New Hire"
        ):
            raise PermissionDenied()
        self.added_context["gigs"] = list(
            set(
                Gig.objects.filter(
                    start__gte=timezone.now(), job__employee=None, published=True
                )
            )
        )
        return super().dispatch(request, *args, **kwargs)


class gigList(SLUGSMixin, TemplateView):
    template_name = "gig/list.html"

    def dispatch(self, request, *args, **kwargs):
        self.added_context["gigs"] = Gig.objects.filter(published=True).order_by(
            "-start"
        )[:50]
        return super().dispatch(request, *args, **kwargs)


class staffShow(SLUGSMixin, MultipleFormView):
    template_name = "gig/staff.html"

    def dispatch(self, request, *args, **kwargs):
        self.added_context["gig"] = Gig.objects.get(pk=kwargs["object_id"])
        self.added_context["unfilled_positions"] = [
            [job, []]
            for job in Job.objects.filter(gig=self.added_context["gig"], employee=None)
        ]
        for position in self.added_context["unfilled_positions"]:
            position[1] = Employee.objects.filter(
                pk__in=JobInterest.objects.filter(job=position[0]).values_list(
                    "employee", flat=True
                )
            )
            self.form_classes[f"job_{position[0].pk}"] = {
                "form": StaffShowForm,
                "instance": position[0],
                "kwargs": {"interested_employees": position[1]},
            }
        return super().dispatch(request, *args, **kwargs)

    def process_forms(self, form_instances):
        for form in form_instances["forms"]:
            f = form_instances["forms"][form]
            if f.instance.employee is not None:
                if not f.instance.employee.groups.filter(
                    name=f.instance.position
                ).exists():
                    f.instance.is_test = True
            f.save()
        messages.add_message(
            self.request, messages.SUCCESS, "Selected employees staffed"
        )
        return redirect("admin:gig_gig_change", object_id=self.added_context["gig"].pk)


class SendStaffingEmail(SLUGSMixin, TemplateView):
    template_name = "gig/send_email.html"

    def dispatch(self, request, *args, **kwargs):
        self.added_context["gig"] = Gig.objects.get(pk=kwargs["object_id"])
        self.added_context["request"] = request
        template = get_template("gig/components/staff_email_template.html")
        self.added_context["email_template"] = template.render(self.added_context)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, **kwargs):
        recipient_list = []
        for emp in self.added_context["gig"].job_set.all():
            recipient_list.append(emp.employee.email)
        # subject = f"You've been staffed for {self.added_context['gig'].name}"
        # html_message = self.added_context['email_template']
        # plain_message = strip_tags(html_message)
        # email_from = settings.EMAIL_HOST_USER
        # send_mail(subject, plain_message, email_from, recipient_list, html_message=html_message)
        email = EmailMessage(
            f"You've been staffed for {self.added_context['gig'].name}",
            self.added_context["email_template"],
            "bssl.slugs@binghamtonsa.org",
            [],
            recipient_list,
            reply_to=["bssl@binghamtonsa.org"],
        )
        email.content_subtype = "html"
        email.send()
        messages.add_message(
            self.request, messages.SUCCESS, "Email sent to employees working this show"
        )
        return redirect("admin:gig_gig_change", object_id=self.added_context["gig"].pk)


@method_decorator(xframe_options_exempt, name="dispatch")
class generateEmailTemplate(SLUGSMixin, TemplateView):
    template_name = "gig/components/staff_email_template.html"

    def dispatch(self, request, *args, **kwargs):
        self.added_context["gig"] = Gig.objects.get(pk=kwargs["gig_id"])
        return super().dispatch(request, *args, **kwargs)
