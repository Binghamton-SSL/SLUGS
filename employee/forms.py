from utils.generic_email import send_generic_email
from django.template.loader import get_template
import employee
from django import forms
from django.contrib.auth import password_validation
from django.contrib.admin import widgets
from django.contrib.auth.models import Group
from django.forms.forms import Form
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordChangeForm
from crispy_forms.helper import FormHelper
from django.forms import ModelForm
from employee.models import Employee, Paperwork, PaperworkForm
from crispy_forms.layout import Layout, Div, Field, HTML, Submit


class UserCreationForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """

    error_messages = {
        "password_mismatch": _("The two password fields didn’t match."),
    }
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
        help_text=_("Enter the same password as before, for verification."),
    )

    class Meta:
        model = Employee
        fields = (
            "email",
            "first_name",
            "last_name",
            "bnum",
            "graduation_year",
            "phone_number",
        )
        help_texts = {
            "bnum": "Format: BXXXXXXXXX",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages["password_mismatch"],
                code="password_mismatch",
            )
        return password2

    def _post_clean(self):
        super()._post_clean()
        # Validate the password after self.instance is updated with form data
        # by super().
        password = self.cleaned_data.get("password2")
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error("password2", error)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class userCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                "email",
                Div(
                    Field("password1", wrapper_class="w-full mr-2"),
                    Field("password2", wrapper_class="w-full ml-2"),
                    css_class="flex w-full",
                ),
                Div(
                    "first_name",
                    "last_name",
                ),
                "phone_number",
                "bnum",
                "graduation_year",
                Submit(
                    "submit",
                    "Submit",
                    css_class="bg-white text-black rounded-sm py-2 px-4",
                ),
                css_class="max-w-5xl my-4 mx-auto",
            ),
        )


class userChangeForm(ModelForm):
    class Meta:
        model = Employee
        fields = ["email", "first_name", "last_name", "phone_number", "graduation_year", "signature"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            "email",
            HTML(
                """
                <div onclick="window.location='{% url 'employee:change_password' %}'" class="px-4 py-2 my-2 text-white bg-black rounded-sm cursor-pointer w-max">
                    Change Password
                </div>
                <label for="id_userChangeForm-bnum" class="block mb-2 text-sm font-bold text-gray-700">
                B-Number</label>
                <p class="my-2 text-gray-700">{{request.user.bnum}}</p>
            """  # noqa
            ),
            "graduation_year",
            Div(
                Div("first_name", css_class="flex-1"),
                Div("last_name", css_class="flex-1"),
                css_class="md:flex md:space-x-2",
            ),
            "phone_number",
            Div(
                "signature",
                css_class="border-black border-2 m-2 p-2 rounded-sm"
            ),
            Submit(
                "submit",
                "Update",
                css_class="my-4 bg-black text-white rounded-sm py-2 px-4 cursor-pointer",
            ),
        )


class changePasswordForm(PasswordChangeForm):
    # text-red-500 <- this is required for proper error rendering from tailwind
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                "old_password",
                "new_password1",
                "new_password2",
                Submit(
                    "submit",
                    "Update Password",
                    css_class="bg-white text-black rounded-sm py-2 px-4",
                ),
                css_class="space-y-4",
            ),
        )


class uploadForm(ModelForm):
    class Meta:
        model = PaperworkForm
        fields = ["pdf"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["pdf"].label = "File"
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                "pdf",
                Submit(
                    "submit",
                    "Upload Form",
                    css_class="bg-white text-black rounded-sm py-2 mt-2 px-4",
                ),
            )
        )


class signPaperworkForm(Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Submit(
                "submit",
                "Sign Form using Signature on File",
                css_class="bg-white text-black rounded-sm py-2 mt-2 px-4",
            ),
        )


class massAssignPaperworkForm(Form):
    formstoadd = forms.ModelMultipleChoiceField(
        queryset=Paperwork.objects.all(),
        widget=widgets.FilteredSelectMultiple("Forms to assign", is_stacked=False),
    )
    ids = forms.CharField(widget=forms.HiddenInput())

    def add_forms(self, request):
        for empid in self.cleaned_data["ids"].split(","):
            forms = []
            attachments = []
            for form in self.cleaned_data["formstoadd"]:
                emp = Employee.objects.get(pk=empid)
                pform = PaperworkForm(form=form, employee=emp)
                pform.save()
                forms.append(pform)
                attachments.append(pform.form.form_pdf.file.name)
            template = get_template("employee/components/general_forms.html")
            email_template = template.render({"request": request})
            send_generic_email(
                request=request,
                subject=f"[ACTION REQUIRED] New forms to fill out on SLUGS",
                title=f"Paperwork needed: {', '.join([f.form.form_name for f in forms])}",
                included_html=email_template,
                included_text=f"How's it going {emp.first_name}, <br><br> Attached (and on SLUGS) you'll find a/some new form(s) we need you to fill out. You can upload it to SLUGS by clicking the button above or by going to the 'You' tab in SLUGS and clicking on the appropriate document under the 'Paperwork' section.<br><br>Thanks!<br>",  # noqa
                to=[emp.email],
                attachments=attachments,
            )

    class Meta:
        fields = ["formstoadd", "ids"]


class addGroupsForm(Form):
    groups_to_add = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=widgets.FilteredSelectMultiple("Groups to add", is_stacked=False),
    )
    ids = forms.CharField(widget=forms.HiddenInput())

    def add_groups(self, request):
        for empid in self.cleaned_data["ids"].split(","):
            for group in self.cleaned_data["groups_to_add"]:
                emp = Employee.objects.get(pk=empid)
                group.user_set.add(emp)

    class Meta:
        fields = ["groups_to_add", "ids"]
