from django.views.generic.edit import FormView
from django.contrib import messages
from equipment.models import System
from equipment.forms import reportSystemBrokenForm
from django.urls import reverse_lazy
from SLUGS.views import SLUGSMixin
from utils.generic_email import send_generic_email
from django.utils.translation import gettext_lazy as _


# Create your views here.
class reportBroken(SLUGSMixin, FormView):
    form_class = reportSystemBrokenForm
    template_name = "equipment/report.html"
    success_url = reverse_lazy("index")

    def form_valid(self, form):
        form.save()
        greeting = _("Ayo Shop Techs,")
        email_body = _("""
                %(fullName)s said that %(brokenSystemName)s is broken.
                <br>
                Here are the details:
                <br><br>
                Notes: <br> <code>%(brokenSystemNotes)s</code>
                <br><br>
                <b>
                Go to SLUGS to start the investigation.
                </b>
        """) % {"fullName": f"{(form.instance.reported_broken_by.preferred_name if form.instance.reported_broken_by.preferred_name else form.instance.reported_broken_by.first_name)} {form.instance.reported_broken_by.last_name}",
                "brokenSystemName": form.instance.broken_system,
                "brokenSystemNotes": form.instance.notes}
        send_generic_email(
            request=None,
            title=f"EQUIPMENT BROKEN - {form.instance.broken_system.get_department_display()} - {form.instance.broken_system.name}",
            included_text=(greeting + "<br><br>" + email_body),
            subject=f"[SLUGS] EQUIPMENT BROKEN - {form.instance.broken_system.get_department_display()} - {form.instance.broken_system.name}",
            to=["bssl@binghamtonsa.org"],
        )
        messages.add_message(
            self.request, messages.SUCCESS, "Report successfully submitted"
        )
        return super().form_valid(form)

    def get_initial(self):
        return {
            "status": "U",
            "reported_broken_by": self.request.user,
            "broken_system": self.kwargs["system_id"],
        }

    def dispatch(self, request, *args, **kwargs):
        self.added_context["system"] = System.objects.get(pk=kwargs["system_id"])
        return super().dispatch(request, *args, **kwargs)
