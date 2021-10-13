from copy import deepcopy

from django.utils import timezone
from training.models import Trainee
from gig.models import Job
from finance.models import PayPeriod, Shift, Wage
from employee.models import Employee, OfficeHours


def getShiftsForEmployee(emp):
    shifts = Shift.objects.none()
    # Training
    for trainee in Trainee.objects.filter(employee=emp):
        shifts = shifts | trainee.shifts.all()
    # Jobs
    for job in Job.objects.filter(employee=emp):
        shifts = shifts | job.shifts.all()
    # Office Hours
    for shift in OfficeHours.objects.filter(employee=emp):
        shifts = shifts | shift.shifts.all()
    shifts.order_by("time_out")[:25]
    return shifts


def prepareSummaryData(pp_id):
    total_hours = 0
    total_sum = 0
    pay_period = PayPeriod.objects.get(pk=pp_id)
    rates = {}
    for rate in Wage.objects.all().order_by("hourly_rate"):
        rates[rate] = [rate, 0]
    employees = {}
    for employee in Employee.objects.all().filter(is_active=True).exclude(groups__name__in=["SA Employee","Awaiting Paperwork"]).order_by("last_name"):
        employees[employee.bnum] = {
            "bnum": employee.bnum,
            "name": f"{employee.first_name} {employee.last_name}",
            "shifts": [],
            "rates": deepcopy(rates),
            "total_amount": 0.00,
            "total_hours": 0.00,
        }
    for shift in pay_period.shifts.all():
        if shift.processed:
            employees[shift.content_object.employee.bnum]["shifts"].append(shift)
            employees[shift.content_object.employee.bnum]["rates"][
                shift.content_object.position.hourly_rate
            ][1] += (round(shift.total_time / timezone.timedelta(minutes=15)) / 4)
            employees[shift.content_object.employee.bnum]["total_amount"] += float(
                shift.content_object.position.hourly_rate.hourly_rate
            ) * (round(shift.total_time / timezone.timedelta(minutes=15)) / 4)
            employees[shift.content_object.employee.bnum]["total_hours"] += (
                round(shift.total_time / timezone.timedelta(minutes=15)) / 4
            )

            total_hours += round(shift.total_time / timezone.timedelta(minutes=15)) / 4
            total_sum += float(
                shift.content_object.position.hourly_rate.hourly_rate
            ) * (round(shift.total_time / timezone.timedelta(minutes=15)) / 4)
    return {
        "rates": rates,
        "employees": employees,
        "pay_period": pay_period,
        "total_sum": total_sum,
        "total_hours": total_hours,
    }
