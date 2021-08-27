from crispy_forms.helper import FormHelper
from gig.models import Gig, Job
import django.forms as forms


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
        empty_label="---------",
        required=True,
        widget=None,
        label=None,
        initial=None,
        help_text="",
        to_field_name=None,
        limit_choices_to=None,
        blank=False,
        **kwargs,
    ):
        self.instance = instance
        super().__init__(queryset)

    def label_from_instance(self, obj):
        return f'{obj}{" - TESTING" if not obj.groups.filter(name=self.instance.position).exists()  else ""}'


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
            instance=instance, queryset=interested_emps
        )
        # self.fields["employee"] = forms.ModelChoiceField(queryset=interested_emps)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
