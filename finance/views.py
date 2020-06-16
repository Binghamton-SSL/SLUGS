from django.shortcuts import render, redirect
from django.urls import reverse
from .models import *
from gig.models import SystemInstance, Shift, Employee
import employee.models as empModels
import io
from django.http import HttpResponse
import xlsxwriter
from collections import defaultdict


# Create your views here.
def estimate(request,invoice_id):
    if empModels.Group.objects.get(name="Manager") not in request.user.groups.all():
        return redirect('%s?next=%s' % (reverse('index'), request.path))
    invoice = Invoice.objects.get(pk=invoice_id)
    gig = invoice.linked_gig
    systems = SystemInstance.objects.filter(linked_gig=gig)
    return render(request, 'finance/estimate.html', {"invoice":invoice,"gig":gig,"systems":systems})

def invoice(request,invoice_id):
    if empModels.Group.objects.get(name="Manager") not in request.user.groups.all():
        return redirect('%s?next=%s' % (reverse('index'), request.path))
    invoice = Invoice.objects.get(pk=invoice_id)
    gig = invoice.linked_gig
    systems = SystemInstance.objects.filter(linked_gig=gig)
    return render(request, 'finance/invoice.html', {"invoice":invoice,"gig":gig,"systems":systems})


def payroll(request,paydate,beg,end):
    if empModels.Group.objects.get(name="Manager") not in request.user.groups.all():
        return redirect('%s?next=%s' % (reverse('index'), request.path))
    emps = {}
    for emp in empModels.Employee.objects.all():
        emps[emp.id] = defaultdict(int)
    for shift in Shift.objects.filter(time_in__range=[beg, end],processed=False):
         employee = Employee.objects.get(id=shift.object_id)
         emps[employee.linked_employee.id][employee.employee_type.hourly_rate.id] += shift.total_hours
         emps[employee.linked_employee.id]['hours'] += shift.total_hours
         emps[employee.linked_employee.id]['gross'] += shift.total_hours*employee.employee_type.hourly_rate.amount

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet("BSSL")
    worksheet.write(0, 0, "BSSL Payroll  - #7400")
    worksheet.write(0, 1, "Paydate")
    worksheet.write(0, 2, f'{paydate:%m-%d-%Y}')
    worksheet.write(0, 3, "Beginning")
    worksheet.write(0, 4, f'{paydate:%m-%d-%Y}')
    worksheet.write(0, 5, "Ending")
    worksheet.write(0, 6, f'{paydate:%m-%d-%Y}')
    col = 1
    for wage_type in empModels.Wage.objects.all():
        worksheet.write(2,wage_type.id, f'{wage_type.name}\n{wage_type.amount}')
        col += wage_type.id
    worksheet.write(2,col,"Reg Hours")
    worksheet.write(2,col+1,"OT Hours")
    worksheet.write(2,col+2,"Gross Pay")
    row = 3
    worksheet.write(2,0,"Name / Rate")
    for emp in empModels.Employee.objects.all():
        worksheet.write(row,0, str(emp))
        col = 0
        for wage_type in empModels.Wage.objects.all():
            worksheet.write(row,wage_type.id, emps[emp.id][wage_type.id])
            col = wage_type.id
        worksheet.write(row,col+1, emps[emp.id]['hours'])
        worksheet.write(row,col+3, f"${round(emps[emp.id]['gross'],2)}")
        row += 1
    workbook.close()
    output.seek(0)
    filename = 'payroll.xlsx'
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=%s' % filename

    return response