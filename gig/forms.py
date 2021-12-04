from crispy_forms.helper import FormHelper
from gig.models import Gig, Job, JobInterest
from employee.models import Employee
import django.forms as forms
from django.contrib.humanize.templatetags import humanize
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
            f'staffing score: {functools.reduce(lambda a, b: a+(1 if Job.objects.filter(employee=obj, gig__pk=b[0]).first() is not None else -1), JobInterest.objects.filter(employee=obj).values_list("job__gig").distinct(), 0)*(timezone.now() - Job.objects.filter(employee=obj).order_by("-gig__start").first().gig.start).days}, '  # Reduce all job interests, add 1 for every gig staffed and -1 for every gig skipped. Multiply by last time staffed to account for multiple jobs on same gig (can't be staffed more than once)
            # f'Staffed {round(Job.objects.filter(employee=obj).count()/JobInterest.objects.filter(employee=obj).count()*100,2)}% of time,' # Old percentage based score
            f'last staffed {str((timezone.now() - Job.objects.filter(employee=obj).order_by("-gig__start").first().gig.start).days)+" days ago" if (timezone.now() - Job.objects.filter(employee=obj).order_by("-gig__start").first().gig.start).days > 0 else "in the future" if Job.objects.filter(employee=obj).order_by("-gig__start").first() is not None else "never" }'
        )


class StaffShowForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ("employee",)

    def __init__(self, *args, **kwargs):
        interested_emps = kwargs.pop("interested_employees", "")
        instance = kwargs["instance"]
        # emp_choices = [
        #     (
        #         o.pk,
        #         str(o)
        #         if o.groups.filter(name=instance.position).exists()
        #         else str(o) + " - Testing",
        #     )
        #     for o in interested_emps
        # ]
        # emp_choices.append((None, "---------"))
        super().__init__(*args, **kwargs)
        # self.fields["employee"] = forms.ChoiceField(
        #     choices=emp_choices, label="Assigned Employee", required=False
        # )
        self.fields["employee"] = StaffModelChoiceField(
            instance=instance, queryset=interested_emps, required=False
        )
        # self.fields["employee"] = forms.ModelChoiceField(queryset=interested_emps)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
