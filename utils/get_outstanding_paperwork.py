from employee.models import Employee

for emp in Employee.objects.filter(is_active=True):
    is_good = True
    paperwork_missing = []
    for paperwork in emp.paperworkform_set.all():
        if  not paperwork.processed:
            is_good = False
            paperwork_missing.append(paperwork.form.form_name)
    if not is_good:
        # print(f'{emp.first_name} {emp.last_name} - {", ".join(paperwork_missing)}')
        print(f'{emp.first_name} {emp.last_name}')