from django import forms
from django.forms import modelformset_factory
from django.forms import BaseModelFormSet
from finance.models import PayPeriod, Shift
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit


class BaseShiftForm(forms.ModelForm):
    class Meta:
        widgets = {
            "time_in": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "w-72"},
                format="%Y-%m-%dT%H:%M:%S",
            ),
            "time_out": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "w-72"},
                format="%Y-%m-%dT%H:%M:%S",
            ),
        }


class BaseShiftFormset(BaseModelFormSet):
    pass


ShiftFormSet = modelformset_factory(
    Shift,
    fields=("time_in", "time_out"),
    form=BaseShiftForm,
    formset=BaseShiftFormset,
    extra=1,
    can_delete=True,
)


class rollOverShiftsForm(forms.Form):
    pay_period = forms.ModelChoiceField(
        queryset=PayPeriod.objects.all(),
        label="Pay Period to move shifts to"
    )
    shifts = forms.ModelMultipleChoiceField(
        queryset=Shift.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Shifts you want to rollover",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(args, kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            "pay_period",
            "shifts",
            Submit(
                "submit",
                "Roll Over Shifts",
                css_class="rounded-sm text-white bg-green px-4 py-2",
            ),
        )
