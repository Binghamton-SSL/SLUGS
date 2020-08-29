from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from .forms import ReportBrokenEquipmentForm
from .models import Gig, Employee, SystemInstance, Signup, InterestedEmployee, System, Shift
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
import datetime
import json


def index(request):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % (reverse('auth:login'), request.path))
    gigs = Gig.objects.all().order_by('-start')
    return render(request, 'gig/index.html', {'gigs': gigs})


def gigIndex(request,gig_id):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % (reverse('auth:login'), request.path))
    gig = Gig.objects.get(pk=gig_id)
    message=False
    if request.method == 'POST':
        for obj in request.POST:
            if obj[0] == 'e':
                data = obj.split('-')
                if data[2] == 'in':
                    try:
                        nShift = Shift(
                            time_in = datetime.datetime.strptime(request.POST[obj],'%Y-%m-%dT%H:%M'),
                            time_out = datetime.datetime.strptime(request.POST['e-{}-{}-{}'.format(data[1],'out',data[3])],'%Y-%m-%dT%H:%M'),
                            content_type = ContentType.objects.get(model="employee",app_label="gig"),
                            content_object = Employee.objects.get(id=data[1]),
                        )
                        if (nShift.time_out-nShift.time_in).total_seconds() <= 0.0:
                            raise Exception()
                        nShift.save()
                        message = {
                            "type": "uk-alert-success",
                            "message": "Day of Show has been updated."
                        }
                    except:
                        message = {
                            "type": "uk-alert-danger",
                            "message": "You improperly formatted / forgot to fill out a time in/out field."
                        }
                       
            elif obj[0] == 'c':
                pass
            elif obj[0] == 'd':
                gig.day_of_show_notes = request.POST[obj]
                gig.save()
            else:
                data = obj.split('-')
                if data[1] == 'in':
                    try:
                        oShift = Shift.objects.get(id=data[0])
                        oShift.time_in = datetime.datetime.strptime(request.POST[obj],'%Y-%m-%dT%H:%M')
                        oShift.time_out = datetime.datetime.strptime(request.POST['{}-out'.format(data[0])],'%Y-%m-%dT%H:%M')
                        if (oShift.time_out-oShift.time_in).total_seconds() < 0.0:
                            raise Exception()
                        oShift.save()
                        message = {
                                "type": "uk-alert-success",
                                "message": "Day of Show has been updated."
                            }
                    except:
                        message = {
                            "type": "uk-alert-danger",
                            "message": "You improperly formatted / forgot to fill out a time in/out field."
                        }
                        
    employees = Employee.objects.filter(linked_gig=gig)
    lEmployees = employees.filter(department="L")
    sEmployees = employees.filter(department="S")
    mEmployees = employees.filter(department="M")
    oEmployees = employees.filter(department="O")
    user = employees.filter(linked_employee=request.user)[0] if employees.filter(linked_employee=request.user).exists() else False
    systems = SystemInstance.objects.filter(linked_gig=gig)
    
    if gig.archived:
        message = {
            "type": "normal",
            "message": "This page has been archived. As such, only a manager can make changes to this page."
        }
    # if request.method == 'POST':
    #     form = GigViewForm(request.POST, user=request.user, instance=gig)
    #     if form.is_valid():
    #         return render(request, 'gig/gigindex.html', {'form': form, 'message': "Your information has been updated"})
    #     else:
    #         return render(request, 'gig/gigindex.html', {'form': form, 'messageError': "Your information could NOT be updated"})
    # else:
    #     form = GigViewForm(user=request.user, instance=gig)
    return render(request, 'gig/gigindex.html', {'message': message,'showEmployee': user, 'gig': gig, 'employees': employees, 'lEmployees': lEmployees, 'sEmployees': sEmployees, 'mEmployees': mEmployees, 'oEmployees': oEmployees, 'systems': systems})

@csrf_exempt
def signup(request):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % (reverse('auth:login'), request.path))
    if request.user.groups.all().filter(name = 'New Hire').exists():
        raise PermissionDenied
    if not Signup.objects.get(id=1).is_open:
        raise PermissionDenied
    if request.method == 'POST':
        msg = json.loads(request.body.decode("utf-8"))
        try:
            if msg['value']:
                interest = InterestedEmployee(
                    job=Employee.objects.get(id=msg['id']),
                    linked_employee=request.user,
                )
                interest.save()
                
            else:
                InterestedEmployee.objects.filter(linked_employee=request.user).filter(job=Employee.objects.get(id=msg['id']))[0].delete()
            data = {"status":200,"message":"Update successful","short_message":"✔️"}
        except:
            data = {"status":400,"message":"There was an error :(","short_message":"There was an error :("}
        data = json.dumps(data)
        return HttpResponse(data,'application/json')
            
    start_range = datetime.date.today()
    end_range = start_range + datetime.timedelta(7)
    gigs = Gig.objects.filter(start__range=[start_range, end_range])
    for gig in gigs:
        gig.employees = Employee.objects.filter(linked_gig=gig)
        for emp in gig.employees:
            emp.isIntersted = InterestedEmployee.objects.filter(linked_employee=request.user,job=emp).filter(job=emp).exists()
    return render(request, 'gig/signup.html', {'gigs': gigs})

def reportBrokenEquipment(request,system_id):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % (reverse('auth:login'), request.path))
    if request.method == 'POST':
        form = ReportBrokenEquipmentForm(request.POST)
        if form.is_valid():
            report = form.save()
            report.reported_broken_by = request.user
            report.status = "U"
            report.save()
            return render(request, 'gig/report-broken.html', {'system_id': system_id,'form': form, 'message': "Thank you! suWe'll look into it!"})
    else:
        form = ReportBrokenEquipmentForm(initial={'broken_system': System.objects.get(id=system_id)})
        return render(request, 'gig/report-broken.html', {'system_id': system_id,'form': form})

def punch(request):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % (reverse('auth:login'), request.path))
    message = False
    hired_employee = Employee.objects.get(not_associated_with_event=True,linked_employee=request.user)
    if request.method == 'POST':
        print(hired_employee)
        for obj in request.POST:
            if obj[0] == 'e':
                data = obj.split('-')
                if data[2] == 'in':
                    try:
                        nShift = Shift(
                            time_in = datetime.datetime.strptime(request.POST[obj],'%Y-%m-%dT%H:%M'),
                            time_out = datetime.datetime.strptime(request.POST['e-{}-{}-{}'.format(data[1],'out',data[3])],'%Y-%m-%dT%H:%M'),
                            content_type = ContentType.objects.get(model="employee",app_label="gig"),
                            content_object = hired_employee,
                        )
                        if (nShift.time_out-nShift.time_in).total_seconds() <= 0.0:
                            raise Exception()
                        nShift.save()
                        messages.success(request,"Your timesheet has been updated")
                    except:
                        messages.error(request,"There was an issue processing that request")
                       
            elif obj[0] == 'c':
                pass
            else:
                data = obj.split('-')
                if data[1] == 'in':
                    try:
                        oShift = Shift.objects.get(id=data[0])
                        oShift.time_in = datetime.datetime.strptime(request.POST[obj],'%Y-%m-%dT%H:%M')
                        oShift.time_out = datetime.datetime.strptime(request.POST['{}-out'.format(data[0])],'%Y-%m-%dT%H:%M')
                        if (oShift.time_out-oShift.time_in).total_seconds() < 0.0:
                            raise Exception()
                        oShift.save()
                        messages.success(request,"Your timesheet has been updated")
                    except:
                        messages.error(request,"There was an issue processing that request")
    unpaid_shifts = Shift.objects.filter(processed=False, object_id=hired_employee.id)
    return render(request, 'gig/punch.html', {"shifts": unpaid_shifts})