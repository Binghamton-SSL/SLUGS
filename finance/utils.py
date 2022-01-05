from copy import deepcopy

from django.utils import timezone
from training.models import Trainee
from gig.models import Job
from finance.models import HourlyRate, PayPeriod, Shift, TimeSheet, Wage
from employee.models import Employee, OfficeHours
from django.db.models import Q


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
    employees = {}

    try:
        for employee in (
            Employee.objects.all()
            .filter(is_active=True)
            .exclude(groups__name__in=["SA Employee", "Awaiting Paperwork"])
            .order_by("last_name")
        ):
            employees[employee.bnum] = {
                "bnum": employee.bnum,
                "name": f"{employee.first_name} {employee.last_name}",
                "shifts": [],
                "rates": {},
                "total_amount": 0.00,
                "total_hours": 0.00,
            }
        if TimeSheet.objects.filter(paid_during=pay_period, employee=employee).exists():
            if TimeSheet.objects.get(paid_during=pay_period, employee=employee).signed is not None:
                for shift in pay_period.shifts.all():
                    if shift.processed:
                        rate_of_pay = HourlyRate.objects.get(
                            Q(wage=shift.content_object.position.hourly_rate)
                            &
                            Q(date_active__lte=shift.time_in)
                            &
                            (
                                Q(date_inactive__gt=shift.time_in)
                                |
                                Q(date_inactive=None)
                            )
                        )
                        if rate_of_pay not in rates:
                            rates[rate_of_pay] = [rate_of_pay, 0]
                        if rate_of_pay not in employees[shift.content_object.employee.bnum]["rates"]:
                            employees[shift.content_object.employee.bnum]["rates"][rate_of_pay] = [rate_of_pay, 0]
                        employees[shift.content_object.employee.bnum]["rates"][rate_of_pay][1] += (
                            round(shift.total_time / timezone.timedelta(minutes=15)) / 4
                        )
                        employees[shift.content_object.employee.bnum]["shifts"].append(shift)
                        employees[shift.content_object.employee.bnum]["total_amount"] += float(
                            rate_of_pay.hourly_rate
                        ) * (round(shift.total_time / timezone.timedelta(minutes=15)) / 4)
                        employees[shift.content_object.employee.bnum]["total_hours"] += (
                            round(shift.total_time / timezone.timedelta(minutes=15)) / 4
                        )

                        total_hours += (
                            round(shift.total_time / timezone.timedelta(minutes=15)) / 4
                        )
                        total_sum += float(
                            rate_of_pay.hourly_rate
                        ) * (round(shift.total_time / timezone.timedelta(minutes=15)) / 4)
        return {
            "rates": rates,
            "employees": employees,
            "pay_period": pay_period,
            "total_sum": total_sum,
            "total_hours": total_hours,
        }
    except:
        total_hours = 0
        total_sum = 0
        for employee in (
            Employee.objects.all()
            .filter(is_active=True)
            .exclude(groups__name__in=["SA Employee"])
            .order_by("last_name")
        ):
            employees[employee.bnum] = {
                "bnum": employee.bnum,
                "name": f"{employee.first_name} {employee.last_name}{' (Outstanding Paperwork)' if employee.groups.filter(name='Awaiting Paperwork').count() > 0 else ''}",
                "shifts": [],
                "rates": rates,
                "total_amount": 0.00,
                "total_hours": 0.00,
            }
        for shift in pay_period.shifts.all():
            if shift.processed:
                rate_of_pay = HourlyRate.objects.get(
                    Q(wage=shift.content_object.position.hourly_rate)
                    &
                    Q(date_active__lte=shift.time_in)
                    &
                    (
                        Q(date_inactive__gt=shift.time_in)
                        |
                        Q(date_inactive=None)
                    )
                )
                if rate_of_pay not in rates:
                    rates[rate_of_pay] = [rate_of_pay, 0]
                if rate_of_pay not in employees[shift.content_object.employee.bnum]["rates"]:
                    employees[shift.content_object.employee.bnum]["rates"][rate_of_pay] = [rate_of_pay, 0]
                employees[shift.content_object.employee.bnum]["shifts"].append(shift)
                employees[shift.content_object.employee.bnum]["total_amount"] += float(
                    rate_of_pay.hourly_rate
                ) * (round(shift.total_time / timezone.timedelta(minutes=15)) / 4)
                employees[shift.content_object.employee.bnum]["total_hours"] += (
                    round(shift.total_time / timezone.timedelta(minutes=15)) / 4
                )

                total_hours += (
                    round(shift.total_time / timezone.timedelta(minutes=15)) / 4
                )
                total_sum += float(
                    rate_of_pay.hourly_rate
                ) * (round(shift.total_time / timezone.timedelta(minutes=15)) / 4)
        return {
            "rates": rates,
            "employees": employees,
            "pay_period": pay_period,
            "total_sum": total_sum,
            "total_hours": total_hours,
        }
