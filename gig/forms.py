from crispy_forms.helper import FormHelper
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from gig.models import Gig, Job, JobInterest
import django.forms as forms
from django.utils import timezone
import functools


class shiftFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_tag = False
        self.disable_csrf = True
        self.render_required_fields = True


class engineerNotesForm(forms.ModelForm):
    class Meta:
        model = Gig
        fields = ("day_of_show_notes",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True


class StaffModelChoiceField(forms.ModelChoiceField):
    instance = None

    def __init__(
        self,
        queryset,
        instance,
        *,
        required=False,
        widget=None,
        label=None,
        help_text="",
        to_field_name=None,
        limit_choices_to=None,
        **kwargs,
    ):
        self.instance = instance
        super().__init__(queryset, empty_label="TBD", required=False)

    def label_from_instance(self, obj):
        return (
            f'{"TESTING - " if not obj.groups.filter(name=self.instance.position).exists()  else ""}'
            f"{obj}"
            f'staffing score: {functools.reduce(lambda a, b: a+(1 if Job.objects.filter(employee=obj, gig__pk=b[0]).first() is not None else -1), JobInterest.objects.filter(employee=obj).values_list("job__gig").distinct(), 0)*((timezone.now() - Job.objects.filter(employee=obj).order_by("-gig__start").first().gig.start).days if Job.objects.filter(employee=obj).order_by("-gig__start").first() is not None else 0)}, '  # Reduce all job interests, add 1 for every gig staffed and -1 for every gig skipped. Multiply by last time staffed to account for multiple jobs on same gig (can't be staffed more than once)
            f'last staffed {(str((timezone.now() - Job.objects.filter(employee=obj).order_by("-gig__start").first().gig.start).days) if Job.objects.filter(employee=obj).order_by("-gig__start").first() is not None else "NEVER") +" days ago" if (((timezone.now() - Job.objects.filter(employee=obj).order_by("-gig__start").first().gig.start).days) if Job.objects.filter(employee=obj).order_by("-gig__start").first() is not None else 0) > 0 else "in the future" if Job.objects.filter(employee=obj).order_by("-gig__start").first() is not None else "never" }'
        )


class StaffShowForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ("employee",)

    def __init__(self, *args, **kwargs):
        interested_emps = kwargs.pop("interested_employees", "")
        instance = kwargs["instance"]
        super().__init__(*args, **kwargs)
        self.fields["employee"] = StaffModelChoiceField(
            instance=instance, queryset=interested_emps, required=False
        )
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True


class GigLoadinChangeForm(BaseInlineFormSet):
    def clean(self):
        super(GigLoadinChangeForm, self).clean()
        if self.is_valid():
            for form in self.cleaned_data:
                if not form["DELETE"]:
                    self.instance.__loadin_depts__.append(form["department"])


class GigJobChangeForm(BaseInlineFormSet):
    def clean(self):
        super(GigJobChangeForm, self).clean()
        if self.is_valid():
            for form in self.cleaned_data:
                dept = form["department"]
                valid_depts = self.instance.gig.__loadin_depts__
                if dept not in valid_depts and not form["DELETE"]:
                    raise ValidationError(
                        f"All jobs should match their parent systems or at least have a load in associated with their department. The current department choice for this job does not have a loadin."
                    )


class GigSystemsChangeForm(BaseInlineFormSet):
    def clean(self):
        super(GigSystemsChangeForm, self).clean()
        for form in self.cleaned_data:
            system = form["system"]
            valid_depts = self.instance.__loadin_depts__
            if system.department not in valid_depts and not form["DELETE"]:
                raise ValidationError(
                    f"A loadin is required for each department that is working the show. Saving would create a situation where {system.get_department_display()} does not have a loadin."
                )


class sendStaffingEmailForm(forms.Form):
    employees_working = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple, label="", choices=["something has gone very wrong", "test hello"]
    )

    def __init__(self, *args, **kwargs):
        employees = kwargs.pop("employees")
        super().__init__(*args, **kwargs)
        self.fields["employees_working"].choices = [
            (emp[3], f"{emp[0] if emp[0] else emp[1]} {emp[2]}") for emp in employees
        ]
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
