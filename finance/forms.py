from django import forms
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from django.forms import BaseModelFormSet
from finance.models import PayPeriod, Shift
from gig.models import Job
from employee.models import OfficeHours
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from django.db.models import Q


class BaseShiftForm(forms.ModelForm):
    class Meta:
        widgets = {
            "time_in": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "w-72", "step": "1"},
                format="%Y-%m-%dT%H:%M:%S",
            ),
            "time_out": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "w-72", "step": "1"},
                format="%Y-%m-%dT%H:%M:%S",
            ),
        }


class BaseShiftFormset(BaseModelFormSet):
    def clean(self):
        super(BaseShiftFormset, self).clean()
        if self.cleaned_data is None:
            raise ValidationError("Data didn't reach server. Try again.")
        for shift in self.cleaned_data:
                employee = None
                # if gig job, use that ref
                if self.prefix.split('_')[0] == 'job':
                    employee = Job.objects.get(pk=self.prefix.split('_')[-1]).employee
                # otherwise fallback to an office hour
                elif self.prefix.split('_')[0] == 'office':
                    employee = OfficeHours.objects.get(pk=self.prefix.split('_')[-1]).employee
                # if all else fails, fallback to self ref
                else:
                    employee = shift["id"].content_object.employee
                if shift:
                    if "time_out" not in shift:
                        shifts = Shift.objects.filter(
                            (
                                Q(time_in__lt=shift["time_in"])
                                & Q(time_out__gt=shift["time_in"])
                            )  # Ends during this shift
                        )
                        if "id" in shift and shift["id"] is not None:
                            shifts = shifts.filter(~Q(pk=shift["id"].pk))
                        for s in shifts:
                            if s.content_object.employee == employee:
                                # pass
                                raise ValidationError(
                                    "Overlapping shifts. Please correct and try again"
                                )
                    else:
                        if (
                            shift["time_in"] is not None
                            and shift["time_out"] is not None
                        ):
                            shifts = Shift.objects.filter(
                                (
                                    (
                                        Q(time_in__lt=shift["time_in"])
                                        & Q(time_out__gt=shift["time_in"])
                                    )  # Ends during this shift
                                    | (
                                        Q(time_in__gt=shift["time_in"])
                                        & Q(time_out__lt=shift["time_out"])
                                    )  # entirely during this shift
                                    | (
                                        Q(time_in__lt=shift["time_in"])
                                        & Q(time_out__gt=shift["time_out"])
                                    )
                                    | (
                                        Q(time_in__lt=shift["time_out"])
                                        & Q(time_out__gt=shift["time_out"])
                                    )  # Starts during this shift
                                )
                            )
                            if "id" in shift and shift["id"] is not None:
                                shifts = shifts.filter(~Q(pk=shift["id"].pk))
                            for s in shifts:
                                if s.content_object.employee == employee:
                                    raise ValidationError(
                                        "Overlapping shifts. Please correct and try again"
                                    )

ShiftFormSet = modelformset_factory(
    Shift,
    fields=("time_in", "time_out"),
    form=BaseShiftForm,
    formset=BaseShiftFormset,
    extra=1,
    can_delete=True,
)

OfficeHoursShiftFormSet = modelformset_factory(
    Shift,
    fields=("time_in", "time_out", "description"),
    form=BaseShiftForm,
    formset=BaseShiftFormset,
    extra=1,
    can_delete=True,
)


class rollOverShiftsForm(forms.Form):
    pay_period = forms.ModelChoiceField(
        queryset=PayPeriod.objects.all(), label="Pay Period to move shifts to"
    )
    shifts = forms.ModelMultipleChoiceField(
        queryset=Shift.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Shifts you want to rollover",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
