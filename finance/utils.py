from copy import deepcopy
from django.utils import timezone
from finance.models import HourlyRate, PayPeriod, Shift, TimeSheet
from employee.models import Employee
from django.db.models import Q, Sum
import decimal


def getShiftsForEmployee(emp):
    return Shift.objects.filter(
            (
                Q(office_hours__employee=emp)
                |
                Q(job__employee=emp)
                |
                Q(trainee__employee=emp)
            )
    ).all()


# Attempts to grab everyone that is squared away with paperwork only. If someone who has outstanding paperwork is in pay period grab everyone on staff. If someone who is no longer on staff is in pay period grab everyone
def prepareSummaryData(pp_id):
    # TODO CLEAN IT UP
    total_hours = 0
    total_sum = decimal.Decimal(0.00)
    pay_period = PayPeriod.objects.get(pk=pp_id)
    rates = {}
    employees = {}
    has_payments = False

    for employee in (
        Employee.objects.filter(timesheet__paid_during=pay_period)
        .exclude(groups__name__in=["SA Employee"])
        .order_by("last_name")
    ):
        employees[employee.bnum] = {
            "bnum": employee.bnum,
            "paychex_flex_workerID": employee.paychex_flex_workerID,
            "name": f"{employee.first_name} {employee.last_name}{' (Outstanding Paperwork)' if employee.groups.filter(name='Awaiting Paperwork').count() > 0 else ''}",
            "shifts": [],
            "rates": deepcopy(rates),
            "total_payments": decimal.Decimal(0.00),
            "total_amount": decimal.Decimal(0.00),
            "total_hours": 0.00,
        }

    # Grab our "base" rates, all rates active during pay period
    for rate in HourlyRate.objects.filter(
        Q(date_active__lte=pay_period.start)
        & (Q(date_inactive__gt=pay_period.start) | Q(date_inactive=None))
    ):
        rates[rate] = [rate, 0]

    for timesheet in TimeSheet.objects.filter(
        paid_during=pay_period,
        signed__isnull=False
    ):
        # For each shift that's signed off
        for shift in timesheet.shifts.all():
            rate_of_pay = shift.content_object.position.hourly_rate.get_price_at_date(shift.time_in)
            # If not tracking rate, add it to our list
            if rate_of_pay not in rates:
                rates[rate_of_pay] = [rate_of_pay, 0]
            # If not tracking rate for employee, add it to their list
            if (rate_of_pay not in employees[shift.content_object.employee.bnum]["rates"]):
                employees[shift.content_object.employee.bnum]["rates"][rate_of_pay] = [rate_of_pay, 0]
            # Add to total hours for rate to employee instance
            employees[shift.content_object.employee.bnum]["rates"][
                rate_of_pay
            ][1] += (
                round(shift.total_time / timezone.timedelta(minutes=15))
                / 4
            )
            employees[shift.content_object.employee.bnum][
                "shifts"
            ].append(shift)
            employees[shift.content_object.employee.bnum][
                "total_hours"
            ] += (
                round(shift.total_time / timezone.timedelta(minutes=15))
                / 4
            )

            total_hours += (
                round(shift.total_time / timezone.timedelta(minutes=15))
                / 4
            )

        payment_total = timesheet.payments.all().aggregate(Sum("amount"))["amount__sum"]
        if (payment_total):
            employees[timesheet.employee.bnum]["total_payments"] += payment_total
            has_payments = True

        employees[timesheet.employee.bnum][
                "total_amount"
            ] += timesheet.cost()
        total_sum += timesheet.cost()

    return {
        "rates": dict(
            sorted(rates.items(), key=lambda rate: rate[1][0].hourly_rate)
        ),
        "employees": employees,
        "pay_period": pay_period,
        "total_sum": total_sum,
        "total_hours": total_hours,
        "has_payments": has_payments,
    }
