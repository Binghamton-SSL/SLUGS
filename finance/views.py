from finance.estimate_data_utils import calculateGigCost
from django.http.response import HttpResponse
from finance.utils import prepareSummaryData
from finance.forms import rollOverShiftsForm
from django.views.generic.base import TemplateView
from django.core.exceptions import PermissionDenied
import django.utils.timezone as timezone
import pytz
import csv
from datetime import datetime
from django.db.models import Q
from django.views import View
from django.conf import settings
from django.http import FileResponse
from django.db.models import Sum
from django.views.generic.edit import FormView
from SLUGS.views import SLUGSMixin
from SLUGS.templatetags.grouping import has_group
from finance.models import Estimate, SystemInstance, PayPeriod, Shift, Wage
from employee.models import Employee
import decimal


class viewEstimate(SLUGSMixin, TemplateView):
    template_name = "finance/estimate.html"
    added_context = {"systems": {}, "fees": {}}

    def dispatch(self, request, *args, **kwargs):
        Estimate.objects.get(pk=kwargs["e_id"]).save()
        self.added_context = calculateGigCost(Estimate.objects.get(pk=kwargs["e_id"]))
        return super().dispatch(request, *args, **kwargs)


class viewInvoice(SLUGSMixin, TemplateView):
    template_name = "finance/invoice.html"
    added_context = {}

    def dispatch(self, request, *args, **kwargs):
        self.added_context = calculateGigCost(Estimate.objects.get(pk=kwargs["e_id"]))
        return super().dispatch(request, *args, **kwargs)


class viewTimesheet(SLUGSMixin, TemplateView):
    template_name = "finance/timesheet.html"

    def dispatch(self, request, *args, **kwargs):
        pay_period = PayPeriod.objects.get(pk=kwargs["pp_id"])
        employee = Employee.objects.get(pk=kwargs["emp_id"])
        shifts = pay_period.shifts.none()
        rates = {}
        for rate in Wage.objects.all().order_by("hourly_rate"):
            rates[rate] = [rate, 0]
        for shift in pay_period.shifts.all():
            if shift.content_object.employee == employee and shift.processed:
                shifts |= Shift.objects.filter(pk=shift.pk)
                rates[shift.content_object.position.hourly_rate][1] += (
                    round(shift.total_time / timezone.timedelta(minutes=15)) / 4
                )
        table_rows = []
        w_num = 1
        w_total = 0
        t_total = 0

        override_shifts = shifts.filter(override_pay_period=pay_period)
        if len(override_shifts) > 0:
            override_start = override_shifts.order_by("time_in").first().time_in
            override_end = override_shifts.order_by("-time_in").first().time_in
            for d in range(
                0,
                int(
                    ((override_end + timezone.timedelta(days=1)) - override_start)
                    / timezone.timedelta(days=1)
                ),
            ):
                day = pytz.timezone("America/New_York").localize(
                    datetime.combine(override_start, datetime.min.time())
                    + timezone.timedelta(days=d)
                )
                s = []
                for shift in shifts.filter(
                    time_in__range=(day, day + timezone.timedelta(minutes=1439))
                ).order_by("time_in"):
                    s.append(
                        (
                            shift,
                            round(shift.total_time / timezone.timedelta(minutes=15))
                            / 4,
                        )
                    )
                    w_total += (
                        round(shift.total_time / timezone.timedelta(minutes=15)) / 4
                    )
                table_rows.append(
                    {"type": "d", "date": day, "name": day.strftime("%A"), "shifts": s}
                )
            table_rows.append(
                {
                    "type": "w",
                    "name": "Overridden Shifts",
                    "total": w_total,
                }
            )
            t_total += w_total
            w_total = 0

        for d in range(
            0,
            int(
                ((pay_period.end + timezone.timedelta(days=1)) - pay_period.start)
                / timezone.timedelta(days=1)
            ),
        ):
            day = pytz.timezone("America/New_York").localize(
                datetime.combine(pay_period.start, datetime.min.time())
                + timezone.timedelta(days=d)
            )
            s = []
            for shift in shifts.filter(
                time_in__range=(day, day + timezone.timedelta(minutes=1439))
            ).order_by("time_in"):
                s.append(
                    (
                        shift,
                        round(shift.total_time / timezone.timedelta(minutes=15)) / 4,
                    )
                )
                w_total += round(shift.total_time / timezone.timedelta(minutes=15)) / 4
            table_rows.append(
                {"type": "d", "date": day, "name": day.strftime("%A"), "shifts": s}
            )
            if (d + 1) % 7 == 0:
                table_rows.append(
                    {
                        "type": "w",
                        "name": f"Week {w_num}",
                        "total": w_total,
                    }
                )
                w_num += 1
                t_total += w_total
                w_total = 0
        table_rows.append(
            {
                "type": "t",
                "name": f"Week{'s' if w_num > 1 else ''} {''.join([f'{num}'+ ('' if w_num-1 == num else ', ' if w_num-2 != num else ' & ') for num in range(1,w_num)])}{' + Overridden Shifts' if len(override_shifts) > 0 else ''}",  # noqa
                "total": t_total,
            }
        )
        self.added_context["shifts"] = shifts
        self.added_context["employee"] = employee
        self.added_context["pay_period"] = pay_period
        self.added_context["table_rows"] = table_rows
        self.added_context["rates"] = rates
        self.added_context["t_total"] = t_total
        self.added_context["t_amt"] = shifts.aggregate(Sum("cost"))
        return super().dispatch(request, *args, **kwargs)


class viewSummary(SLUGSMixin, TemplateView):
    template_name = "finance/summary.html"

    def dispatch(self, request, *args, **kwargs):
        sumData = prepareSummaryData(kwargs["pp_id"])

        self.added_context["rates"] = sumData["rates"]
        self.added_context["employees"] = sumData["employees"]
        self.added_context["pay_period"] = sumData["pay_period"]
        self.added_context["total_sum"] = sumData["total_sum"]
        self.added_context["total_hours"] = sumData["total_hours"]

        return super().dispatch(request, *args, **kwargs)


class exportSummaryCSV(SLUGSMixin, View):
    def dispatch(self, request, *args, **kwargs):
        sumData = prepareSummaryData(kwargs["pp_id"])
        response = HttpResponse(
            content_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="Payroll_Summary_{sumData["pay_period"].start}--{sumData["pay_period"].end}.csv"'
            },
        )

        writer = csv.writer(response)
        writer.writerow(
            ["B-num", "Name"]
            + [f"{rate.name} Hours - ${rate.hourly_rate}" for rate in sumData["rates"]]
            + ["Total Hours", "Gross Pay"]
            + ["Pay Period Start", "Pay Period End", "Payday"]
        )
        writer.writerow(
            ["", ""]
            + ["" for rate in sumData["rates"]]
            + ["", ""]
            + [
                sumData["pay_period"].start,
                sumData["pay_period"].end,
                sumData["pay_period"].payday,
            ]
        )
        for emp in sumData["employees"]:
            emp = sumData["employees"][emp]
            writer.writerow(
                [emp["bnum"], emp["name"]]
                + [
                    "-" if emp["rates"][rate][1] == 0 else emp["rates"][rate][1]
                    for rate in emp["rates"]
                ]
                + [emp["total_hours"], f"${round(emp['total_amount'], 2):,}"]
            )
        writer.writerow(
            ["", ""]
            + ["" for rate in sumData["rates"]][:-1]
            + [
                "Total",
                sumData["total_hours"],
                f'${round(sumData["total_sum"], 2):,}',
            ]
        )
        return response


class RollOverAllShifts(SLUGSMixin, FormView):
    template_name = "finance/rollover.html"
    form_class = rollOverShiftsForm
    success_url = "."

    def dispatch(self, request, *args, **kwargs):
        self.added_context["pay_period"] = PayPeriod.objects.get(pk=kwargs["pp_id"])
        self.added_context["emp"] = Employee.objects.get(pk=kwargs["emp_id"])
        # emp = Employee.objects.get(pk=emp_id)
        # emp_shifts = from_pay_period.shifts.filter(content_object__employee=emp_id)
        # print(emp_shifts)
        return super().dispatch(request, *args, **kwargs)


class EstimateDownload(SLUGSMixin, View):
    def get(self, request, relative_path):
        path = f"{relative_path}"
        absolute_path = "{}/{}".format(settings.MEDIA_ROOT, path)
        response = FileResponse(open(absolute_path, "rb"), as_attachment=True)
        return response


class FinancialOverview(SLUGSMixin, TemplateView):
    template_name = "finance/overview.html"

    def dispatch(self, request, *args, **kwargs):
        if not has_group(request.user, "Financial Director/GM"):
            raise PermissionDenied
        most_recent_pay_period = PayPeriod.objects.all().order_by("-end").first()
        shifts = Shift.objects.filter(
            Q(time_in__gte=most_recent_pay_period.start)
            & Q(time_out__lte=most_recent_pay_period.end + timezone.timedelta(days=1))
        ).order_by("-time_out")
        most_recent_pay_period.shifts.set(shifts)
        most_recent_pay_period.save()
        shifts_hours = shifts.aggregate(Sum("total_time"))
        shifts_price = shifts.aggregate(Sum("cost"))

        self.added_context["most_recent_pay_period"] = most_recent_pay_period
        self.added_context["shifts"] = shifts
        self.added_context["shifts_hours"] = shifts_hours
        self.added_context["shifts_price"] = shifts_price

        return super().dispatch(request, *args, **kwargs)
