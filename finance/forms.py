from django import forms
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from django.forms import BaseModelFormSet
from django.forms.models import BaseInlineFormSet
from finance.models import Shift
from gig.models import Job
from employee.models import OfficeHours
from django.db.models import Q
from nested_admin.formsets import NestedBaseGenericInlineFormSet
import django.utils.timezone as timezone


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
        if not hasattr(self, 'cleaned_data') or self.cleaned_data is None:
            raise ValidationError("Data didn't reach server. Try again.")
        # Must live here and not in model since emp is not set on new shifts
        for idx, shift in enumerate(self.cleaned_data):
            if self.forms[idx].has_changed():
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
                    other_emp_shifts = Shift.objects.all()
                    if shift['id'] is not None:
                        other_emp_shifts = Shift.objects.exclude(pk=shift["id"].pk)
                    else:
                        other_emp_shifts = Shift.objects.all()
                    other_emp_shifts = other_emp_shifts.filter(
                        (
                            Q(office_hours__employee=employee)
                            |
                            Q(job__employee=employee)
                            |
                            Q(trainee__employee=employee)
                        )
                    )
                    if "time_out" not in shift:
                        if(other_emp_shifts.filter(
                            (
                                Q(time_in__lt=shift["time_in"])
                                & Q(time_out__gt=shift["time_in"])
                            )  # Ends during this shift
                        ).count() > 0):
                            self.forms[idx].add_error("__all__", "Overlapping shifts. Please correct and try again")
                            raise ValidationError(
                                    "Overlapping shifts. Please correct and try again"
                                )
                    else:
                        if (
                            shift["time_in"] is not None
                            and shift["time_out"] is not None
                        ):
                            if(other_emp_shifts.filter(
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
                            ).count() > 0):
                                self.forms[idx].add_error("__all__", "Overlapping shifts. Please correct and try again")
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


class PricingChangeForm(BaseInlineFormSet):
    def clean(self):
        super(PricingChangeForm, self).clean()
        for form in self.cleaned_data:
            if ('base_price' in form) and ('price_per-hour' in form):
                if (form['base_price'] + form['price_per_hour'] > max([form['base_price'], form['price_per_hour']])):
                    raise ValidationError(
                        f"There is more than one pricing scheme for a time period. Pricing's can only be of one type per time period."
                    )
                

class ShiftChangeForm(NestedBaseGenericInlineFormSet):
    def clean(self):
        super().clean()
        if self.is_valid():
            for form in self.cleaned_data:
                # Validation: Make sure shift isn't processed
                if form['id'] is not None:
                    if form['id'].processed and form["DELETE"]:
                        raise ValidationError(
                            f"Processed shift from {timezone.template_localtime(form['id'].time_in).strftime('%m/%d/%y %H:%M:%S')} to {timezone.template_localtime(form['id'].time_out).strftime('%m/%d/%y %H:%M:%S')} cannot be deleted once processed. Please contact the Financial Director"
                        )


class HourlyRateChangeForm(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if self.is_valid():
            for form in self.cleaned_data:
                # Validation: Make sure hourly rate isn't used
                if form['id'] is not None:
                    shifts_used = Shift.objects.filter(
                        Q(office_hours__position__hourly_rate=form['id'].wage.pk)
                        |
                        Q(job__position__hourly_rate=form['id'].wage.pk)
                        |
                        Q(trainee__position__hourly_rate=form['id'].wage.pk)
                    )
                    if form['id'].date_inactive:
                        shifts_used = shifts_used.filter(
                            (
                                Q(time_in__gte=form['id'].date_active)
                                &
                                Q(time_in__lte=form['id'].date_inactive)
                            )
                        )
                    else:
                        shifts_used = shifts_used.filter(
                            Q(time_in__gte=form['id'].date_active)
                        )
                    if shifts_used.count() > 0 and form["DELETE"]:
                        raise ValidationError(
                            f"Hourly rate {form['id']} is used in the following shifts: {', '.join([str(shift.pk) for shift in shifts_used])} and cannot be deleted. Please contact the Financial Director"
                        )