import django.forms as forms
from training.models import TrainingRequest
from equipment.models import System
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit


class requestTrainingForm(forms.ModelForm):
    systems = forms.ModelMultipleChoiceField(
        queryset=System.objects.all().order_by("department"),
        widget=forms.CheckboxSelectMultiple,
        label="System(s) you want to learn <br> <span class='text-xs'>If you don't see what you're looking for, just hit anything and type something in the notes</span>",  # noqa
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            "systems",
            "notes",
            Submit(
                "submit",
                "Submit Request",
                css_class="rounded-sm text-white bg-black px-4 py-2",
            ),
        )

    class Meta:
        model = TrainingRequest
        exclude = ["employee"]
