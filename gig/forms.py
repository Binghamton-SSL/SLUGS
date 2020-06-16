from django import forms
from .models import Gig, Employee, BrokenEquipmentReport

class SelectEmployeesForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ('linked_employee',)
    
    def __init__(self, *args, **kwargs):
        interested_emps = kwargs.pop('interested_employees','')
        instance = kwargs.pop('instance','')
        emp_choices = [(o.linked_employee.id, str(o.linked_employee) if o.linked_employee.groups.filter(name = instance.employee_type).exists() else str(o.linked_employee)+" - Testing") for o in interested_emps]
        emp_choices.append((None,"---------"))
        super(SelectEmployeesForm, self).__init__(*args, **kwargs)
        self.fields['linked_employee'] = forms.ChoiceField(
            choices=emp_choices, label='Assigned Employee', required=False
        )

class ReportBrokenEquipmentForm(forms.ModelForm):
    class Meta:
        model = BrokenEquipmentReport
        fields = ('broken_system','notes')
        widgets = {
            'broken_system': forms.Select(attrs={'class': "uk-select"}),
            'notes': forms.Textarea(attrs={'class': "uk-textarea"}),
        }


class GigViewForm(forms.ModelForm):
    class Meta:
        model = Gig
        exclude = ('name',)
        # fields = ('email', 'first_name', 'last_name', 'phone_number')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user','')
        super(GigViewForm, self).__init__(*args, **kwargs)
        # self.fields['employee']=forms.ModelChoiceField(queryset=Employee.objects.filter(linked_employee=user))