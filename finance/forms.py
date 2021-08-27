from django import forms
from django.forms import modelformset_factory
from django.forms import BaseModelFormSet
from finance.models import Shift


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
