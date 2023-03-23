from django.contrib import messages
from django.urls.base import reverse_lazy, reverse
from django.views.decorators.clickjacking import xframe_options_sameorigin, xframe_options_exempt
from employee.forms import signPaperworkForm
from finance.estimate_data_utils import calcuateSubcontractedCost, calculateGigCost
from django.http.response import HttpResponse
from finance.utils import prepareSummaryData
from django.views.generic.base import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect
import django.utils.timezone as timezone
import pytz
import csv
from datetime import datetime
from django.utils.timezone import localtime, now
from django.db.models import Q
from django.views import View
from django.conf import settings
from django.http import FileResponse
from django.db.models import Sum
from django.views.generic.edit import FormView
from SLUGS.views import SLUGSMixin, isAdminMixin
from SLUGS.templatetags.grouping import has_group
from finance.models import Estimate, HourlyRate, PayPeriod, Shift, TimeSheet
from employee.models import Employee
from gig.models import SubcontractedEquipment
from utils.generic_email import send_generic_email
import decimal
import calendar
import barcode


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


class viewSubcontractedEquipment(SLUGSMixin, TemplateView):
    template_name = "finance/subcontracted_equipment.html"
    added_context = {}

    def dispatch(self, request, *args, **kwargs):
        self.added_context = calcuateSubcontractedCost(SubcontractedEquipment.objects.get(pk=kwargs["v_id"]))
        return super().dispatch(request, *args, **kwargs)


class viewTimesheet(SLUGSMixin, TemplateView):
    template_name = "finance/printed_timesheet.html"

    def dispatch(self, request, *args, **kwargs):
        timesheet = TimeSheet.objects.get(pk=kwargs["timesheet_id"])
        barc = barcode.get("code128", str(timesheet.pk))
        barc.default_writer_options.update(
            {
                "module_height": 8.0,
                "font_size": 0,
                "text_distance": 0,
            }
        )
        self.added_context["barcode"] = (
            str(barc.render()).replace("\\n", "").replace("b'", "").replace("'", "")
        )

        if request.user.pk is not None:
            if timesheet.employee.pk != request.user.pk and not (
                has_group(request.user, "Manager")
                or
                has_group(request.user, "SA Employee")
            ):
                raise PermissionDenied()
        shifts = timesheet.shifts.all()
        rates = {}
        table_rows = []
        w_num = 1
        w_total = 0
        w_cost = 0
        t_cost = 0
        t_total = 0

        override_shifts = shifts.filter(override_pay_period__isnull=False)
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
                    rate_of_pay = shift.content_object.position.hourly_rate.get_price_at_date(shift.time_in)
                    if rate_of_pay not in rates:
                        rates[rate_of_pay] = [rate_of_pay, 0, decimal.Decimal(0.00)]
                    rates[rate_of_pay][1] += (
                        round(shift.total_time / timezone.timedelta(minutes=15)) / 4
                    )
                    rates[rate_of_pay][2] += shift.cost
                    s.append(
                        (
                            shift,
                            round(shift.total_time / timezone.timedelta(minutes=15))
                            / 4,
                            shift.cost,
                        )
                    )
                    w_total += (
                        round(shift.total_time / timezone.timedelta(minutes=15)) / 4
                    )
                    w_cost += shift.cost
                if len(s) > 0:
                    table_rows.append(
                        {"type": "d", "date": day, "name": day.strftime("%A"), "shifts": s}
                    )
            table_rows.append(
                {
                    "type": "w",
                    "name": "Overridden Shifts",
                    "total": w_total,
                    "cost": w_cost,
                }
            )
            t_total += w_total
            w_total = 0
            t_cost += w_cost
            w_cost = 0

        for d in range(
            0,
            int(
                ((timesheet.pay_period.end + timezone.timedelta(days=1)) - timesheet.pay_period.start)
                / timezone.timedelta(days=1)
            ),
        ):
            day = pytz.timezone("America/New_York").localize(
                datetime.combine(timesheet.pay_period.start, datetime.min.time())
                + timezone.timedelta(days=d)
            )
            s = []
            for shift in shifts.filter(
                time_in__range=(day, day + timezone.timedelta(minutes=1439))
            ).order_by("time_in"):
                rate_of_pay = shift.content_object.position.hourly_rate.get_price_at_date(shift.time_in)
                if rate_of_pay not in rates:
                    rates[rate_of_pay] = [rate_of_pay, 0, decimal.Decimal(0.00)]
                rates[rate_of_pay][1] += (
                    round(shift.total_time / timezone.timedelta(minutes=15)) / 4
                )
                rates[rate_of_pay][2] += shift.cost
                s.append(
                    (
                        shift,
                        round(shift.total_time / timezone.timedelta(minutes=15)) / 4,
                        shift.cost,
                    )
                )
                w_total += round(shift.total_time / timezone.timedelta(minutes=15)) / 4
                w_cost += shift.cost
            table_rows.append(
                {"type": "d", "date": day, "name": day.strftime("%A"), "shifts": s}
            )
            if (d + 1) % 7 == 0:
                table_rows.append(
                    {
                        "type": "w",
                        "name": f"Week {w_num}",
                        "total": w_total,
                        "cost": w_cost,
                    }
                )
                w_num += 1
                t_total += w_total
                w_total = 0
                t_cost += w_cost
                w_cost = 0
        table_rows.append(
            {
                "type": "t",
                "name": f"Week{'s' if w_num > 1 else ''} {''.join([f'{num}'+ ('' if w_num-1 == num else ', ' if w_num-2 != num else ' & ') for num in range(1,w_num)])}{' + Overridden Shifts' if len(override_shifts) > 0 else ''}",  # noqa
                "total": t_total,
                "cost": t_cost,
            }
        )
        self.added_context["shifts"] = shifts
        self.added_context["employee"] = timesheet.employee
        self.added_context["pay_period"] = timesheet.pay_period
        self.added_context["timesheet"] = timesheet
        self.added_context["table_rows"] = table_rows
        self.added_context["rates"] = dict(
            sorted(rates.items(), key=lambda item: item[0].hourly_rate)
        )
        self.added_context["t_total"] = t_total
        self.added_context["t_amt"] = timesheet.cost()
        self.added_context["payments"] = timesheet.payments.all()
        self.added_context["payment_total"] = timesheet.payments.all().aggregate(Sum("amount"))["amount__sum"]
        return super().dispatch(request, *args, **kwargs)


class ViewTimesheetXframe(viewTimesheet):
    template_name = "finance/timesheet.html"

    @xframe_options_sameorigin
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class SignTimesheet(SLUGSMixin, FormView):
    form_class = signPaperworkForm
    template_name = "finance/sign_timesheet.html"
    success_url = reverse_lazy("employee:overview")

    def dispatch(self, request, *args, **kwargs):
        if request.user.pk is not None:
            self.timesheet = TimeSheet.objects.get(pk=kwargs["timesheet_id"])
            if self.timesheet.employee.pk != request.user.pk:
                raise PermissionDenied()
            self.added_context["timesheet"] = self.timesheet
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.added_context["timesheet"].signed = localtime(now()).date()
        self.added_context["timesheet"].save()
        LogEntry.objects.log_action(
            user_id=self.added_context["timesheet"].employee.pk,
            content_type_id=ContentType.objects.get_for_model(
                self.added_context["timesheet"], for_concrete_model=False
            ).pk,
            object_id=self.added_context["timesheet"].pk,
            object_repr=str(self.added_context["timesheet"]),
            action_flag=CHANGE,
            change_message=f"{self.added_context['timesheet'].employee} signed timesheet electronically.",
        )
        send_generic_email(
            request=None,
            title=f"TIMESHEET SIGNED - {self.added_context['timesheet']}",
            included_text=(
                f"""
                Ayo FD,
                <br><br>
                {(self.added_context['timesheet'].employee.preferred_name if self.added_context['timesheet'].employee.preferred_name else self.added_context['timesheet'].employee.first_name)} {self.added_context['timesheet'].employee.last_name} signed their timesheet for the pay period {self.added_context['timesheet'].pay_period.start} through {self.added_context['timesheet'].pay_period.end}.
                <br><br>
                <b>Go to SLUGS to print it</b>
                <br><br>
                """
            ),  # noqa
            subject=f"[SLUGS] TIMESHEET SIGNED - {self.added_context['timesheet']}",
            to=["bssl.finance@binghamtonsa.org"],
        )
        messages.add_message(
            self.request,
            messages.SUCCESS,
            f"Timesheet: {self.added_context['timesheet'].pay_period} has been signed electronically.",
        )
        return super().form_valid(form)


class viewSummary(SLUGSMixin, isAdminMixin, TemplateView):
    template_name = "finance/summary.html"

    def dispatch(self, request, *args, **kwargs):
        sumData = prepareSummaryData(kwargs["pp_id"])

        self.added_context["rates"] = sumData["rates"]
        self.added_context["employees"] = sumData["employees"]
        self.added_context["pay_period"] = sumData["pay_period"]
        self.added_context["total_sum"] = sumData["total_sum"]
        self.added_context["total_hours"] = sumData["total_hours"]
        self.added_context["has_payments"] = sumData["has_payments"]

        return super().dispatch(request, *args, **kwargs)


class exportSummaryCSV(SLUGSMixin, isAdminMixin, View):
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
            + [
                f"{rate.wage.name} Hours - ${rate.hourly_rate}"
                for rate in sumData["rates"]
            ]
            + ["Total Hours"]
            + (["Payments"] if sumData["has_payments"] else [])
            + ["Gross Pay"]
            + ["Pay Period Start", "Pay Period End", "Payday"]
        )
        writer.writerow(
            ["", ""]
            + ["" for rate in sumData["rates"]]
            + (["", "", ""] if sumData["has_payments"] else ["", ""])
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
                    "-"
                    if (rate not in emp["rates"] or emp["rates"][rate][1] == 0)
                    else emp["rates"][rate][1]
                    for rate in sumData["rates"]
                ]
                + [emp["total_hours"]]
                + ([f"${round(emp['total_payments'], 2)}"] if sumData["has_payments"] else [])
                + [f"${round(emp['total_amount'], 2):,}"]
            )
        writer.writerow(
            ["", ""]
            + ["" for rate in sumData["rates"]][:-1]
            + [
                "Total",
                sumData["total_hours"]]
            + ([""] if sumData["has_payments"] else [])
            + [
                f'${round(sumData["total_sum"], 2)}',
            ]
        )
        return response


class exportSummaryPayChexCSV(SLUGSMixin, isAdminMixin, View):
    def dispatch(self, request, *args, **kwargs):
        sumData = prepareSummaryData(kwargs["pp_id"])
        response = HttpResponse(
            content_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="Payroll_Summary_{sumData["pay_period"].start}--{sumData["pay_period"].end}_PAYCHEX.csv"'
            },
        )

        writer = csv.writer(response)
        columns = ["Company ID", "Worker ID", "Org", "Pay Component", "Rate", "Hours", "Date", "Check Seq Number"]
        writer.writerow(columns)
        for emp in sumData["employees"]:
            emp = sumData["employees"][emp]
            for rate in sumData["rates"]:
                if rate in emp["rates"] and emp["rates"][rate][1] != 0:
                    writer.writerow(
                        [
                            settings.PAYCHEX_COMPANY_ID_HUMAN,  # Company ID
                            emp['paychex_flex_workerID'],  # Worker ID
                            settings.PAYCHEX_ORG_HUMAN,  # Org
                            "Hourly",  # Pay Component
                            rate.hourly_rate,  # Rate
                            emp["rates"][rate][1],  # Hours
                            sumData["pay_period"].payday.strftime("%m/%d/%Y"),  # Date
                            ""  # Check Seq Number
                        ]
                    )
            if emp["total_payments"] > decimal.Decimal(0.00):
                writer.writerow(
                        [
                            settings.PAYCHEX_COMPANY_ID_HUMAN,  # Company ID
                            emp['paychex_flex_workerID'],  # Worker ID
                            settings.PAYCHEX_ORG_HUMAN,  # Org
                            "Bonus",  # Pay Component
                            emp['total_payments'],  # Amount
                            1,  # Qty
                            sumData["pay_period"].payday.strftime("%m/%d/%Y"),  # Date
                            ""  # Check Seq Number
                        ]
                )
        return response


class saBillingSummary(SLUGSMixin, TemplateView):
    template_name = "finance/sa_billing_summary.html"

    def dispatch(self, request, *args, **kwargs):
        month = kwargs["month"]
        year = kwargs["year"]
        estimates = Estimate.objects.filter(
            Q(
                gig__start__month=month,
                gig__start__year=year,
                billing_contact__organization__SA_account_num__isnull=False,
                gig__published=True,
                payment_due=None
            )
            |
            Q(
                payment_due__month=month,
                payment_due__year=year,
                billing_contact__organization__SA_account_num__isnull=False,
                gig__published=True,
            )
        ).order_by("billing_contact__organization")
        groups = {}
        grand_total = decimal.Decimal(0)
        for e in estimates:
            if e.billing_contact.organization not in groups:
                groups[e.billing_contact.organization] = {
                    "estimates": [e],
                    "total": decimal.Decimal(e.outstanding_balance),
                }
            else:
                groups[e.billing_contact.organization]["estimates"].append(e)
                groups[e.billing_contact.organization][
                    "total"
                ] += e.outstanding_balance
            grand_total += e.outstanding_balance
        self.added_context["groups"] = groups
        self.added_context["grand_total"] = grand_total
        self.added_context["month"] = month
        self.added_context["year"] = year
        self.added_context["month_name"] = calendar.month_name[int(month)]
        return super().dispatch(request, *args, **kwargs)


class EstimateDownload(View):

    @xframe_options_exempt
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated and not (request.COOKIES.get('SLUGSKiosk') and Employee.objects.get(pk=request.COOKIES.get('SLUGSKiosk')).is_staff):
            return redirect("%s?next=%s" % (reverse("login"), request.path))
        return super().dispatch(request, *args, **kwargs)

    @xframe_options_exempt
    def get(self, request, relative_path):
        path = f"estimates/{relative_path}"
        absolute_path = "{}/{}".format(settings.MEDIA_ROOT, path)
        response = FileResponse(open(absolute_path, "rb"), as_attachment=False)
        return response


class FinancialOverview(SLUGSMixin, TemplateView):
    template_name = "finance/overview.html"

    def dispatch(self, request, *args, **kwargs):
        if not has_group(request.user, "Financial Director/GM"):
            raise PermissionDenied
        most_recent_pay_period = PayPeriod.objects.filter(end__lte=datetime.now()).order_by("end").last()
        shifts = Shift.objects.filter(
            Q(time_in__gte=most_recent_pay_period.start)
            & Q(time_in__lte=most_recent_pay_period.end + timezone.timedelta(days=1))
        ).order_by("processed", "-time_out")
        shifts_hours = shifts.aggregate(Sum("total_time"))
        shifts_price = shifts.aggregate(Sum("cost"))

        current_pay_period = PayPeriod.objects.filter(end__gte=datetime.now()).order_by("end").last()
        if current_pay_period:
            current_shifts = Shift.objects.filter(
                Q(time_in__gte=current_pay_period.start)
                & Q(time_in__lte=current_pay_period.end + timezone.timedelta(days=1))
            ).order_by("processed", "-time_out")
            current_shifts_hours = current_shifts.aggregate(Sum("total_time"))
            current_shifts_price = current_shifts.aggregate(Sum("cost"))

        unsigned_tms = TimeSheet.objects.filter(signed=None, employee__is_active=True)
        unsigned_abandoned_tms = TimeSheet.objects.filter(signed=None, employee__is_active=False)
        unprocessed_tms = TimeSheet.objects.filter(~Q(signed=None) & Q(processed=None))

        self.added_context["most_recent_pay_period"] = most_recent_pay_period
        self.added_context["shifts"] = shifts
        self.added_context["shifts_hours"] = shifts_hours
        self.added_context["shifts_price"] = shifts_price

        self.added_context["current_pay_period"] = current_pay_period
        self.added_context["current_shifts"] = current_shifts if current_pay_period else None
        self.added_context["current_shifts_hours"] = current_shifts_hours if current_pay_period else None
        self.added_context["current_shifts_price"] = current_shifts_price if current_pay_period else None

        self.added_context["unsigned_tms"] = unsigned_tms
        self.added_context["unsigned_abandoned_tms"] = unsigned_abandoned_tms
        self.added_context["unprocessed_tms"] = unprocessed_tms

        return super().dispatch(request, *args, **kwargs)
