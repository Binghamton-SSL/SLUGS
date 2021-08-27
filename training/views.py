from SLUGS.views import SLUGSMixin
from django.views.generic.edit import FormView
from training.models import Training, TrainingRequest
from training.forms import requestTrainingForm
from django.utils import timezone
from django.contrib import messages


# Create your views here.
class index(SLUGSMixin, FormView):
    form_class = requestTrainingForm
    template_name = "training/index.html"
    success_url = "."

    def form_invalid(self, form):
        messages.error(
            self.request, "Please select a system or two to request training on"
        )
        return super().form_invalid(form)

    def form_valid(self, form):
        print("hello")
        form.instance.employee = self.request.user
        form.save()
        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Request successfully submitted. We'll contact you shortly.",
        )
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        self.added_context["trainings"] = Training.objects.filter(
            date__gte=timezone.now()
        ).order_by("dept")
        self.added_context["trainingRequests"] = TrainingRequest.objects.filter(
            employee=request.user, answered=False
        )
        return super().dispatch(request, *args, **kwargs)
