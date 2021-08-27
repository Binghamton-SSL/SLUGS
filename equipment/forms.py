from django.forms import ModelForm
from equipment.models import BrokenEquipmentReport
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Submit


class reportSystemBrokenForm(ModelForm):
    class Meta:
        model = BrokenEquipmentReport
        exclude = ("investigation",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Field("status", type="hidden"),
                Field("broken_system", type="hidden"),
                Field("reported_broken_by", type="hidden"),
                "notes",
                Submit(
                    "submit",
                    "Submit",
                    css_class="bg-white text-black rounded-sm py-2 px-4",
                ),
                css_class="max-w-5xl my-4 mx-auto",
            ),
        )
