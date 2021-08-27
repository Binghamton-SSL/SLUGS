from django.views.generic.edit import FormView
from django.contrib import messages
from equipment.models import System
from equipment.forms import reportSystemBrokenForm
from django.urls import reverse_lazy
from SLUGS.views import SLUGSMixin


# Create your views here.
class reportBroken(SLUGSMixin, FormView):
    form_class = reportSystemBrokenForm
    template_name = "equipment/report.html"
    success_url = reverse_lazy("index")

    def form_valid(self, form):
        form.save()
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
