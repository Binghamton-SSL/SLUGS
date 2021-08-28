from copy import deepcopy
from django.views.generic.base import TemplateView
from django.core.exceptions import PermissionDenied
import django.utils.timezone as timezone
import pytz
from datetime import datetime
from django.db.models import Q
from django.views import View
from django.conf import settings
from django.http import FileResponse
from django.db.models import Sum
from SLUGS.views import SLUGSMixin
from SLUGS.templatetags.grouping import has_group
from finance.models import Estimate, SystemInstance, PayPeriod, Shift, Wage
from employee.models import Employee
import decimal


class viewEstimate(SLUGSMixin, TemplateView):
    template_name = "finance/estimate.html"
    added_context = {"systems": {}, "fees": {}}

    def dispatch(self, request, *args, **kwargs):
        self.added_context = {"systems": {}, "fees": {}}
        self.added_context["estimate"] = Estimate.objects.get(pk=kwargs["e_id"])
        self.added_context["shop_time"] = (
            self.added_context["estimate"]
            .gig.loadin_set.order_by("shop_time")
            .first()
            .shop_time
        )
        self.added_context["load_in"] = (
            self.added_context["estimate"]
            .gig.loadin_set.order_by("shop_time")
            .first()
            .load_in
        )
        self.added_context["load_out"] = (
            self.added_context["estimate"]
            .gig.loadin_set.order_by("-load_out")
            .first()
            .load_out
        )

        for system in self.added_context["estimate"].gig.systems.all():
            dept = system.department
            rented_start = (
                self.added_context["estimate"]
                .gig.loadin_set.filter(department=dept)
                .order_by("shop_time")
                .first()
                .shop_time
            )
            rented_end = (
                self.added_context["estimate"]
                .gig.loadin_set.filter(department=dept)
                .order_by("-load_out")
                .first()
                .load_out
            )
            time_rented = rented_end - rented_start
            self.added_context["systems"][system] = [
                system,
                decimal.Decimal(time_rented / timezone.timedelta(hours=1)),
                decimal.Decimal(time_rented / timezone.timedelta(hours=1))
                if system.price_per_hour
                else 1,
                round(
                    system.base_price
                    + system.price_per_hour
                    * decimal.Decimal(time_rented / timezone.timedelta(hours=1)),
                    2,
                ),
                False,
            ]
            addons = SystemInstance.objects.get(
                gig=self.added_context["estimate"].gig, system=system
            ).addoninstance_set.all()
            for addon_set_item in addons:
                addon = addon_set_item.addon
                self.added_context["systems"][addon_set_item.pk] = [
                    addon,
                    decimal.Decimal(time_rented / timezone.timedelta(hours=1)),
                    (
                        addon_set_item.qty
                        * decimal.Decimal(time_rented / timezone.timedelta(hours=1))
                    )
                    if addon.price_per_hour != 0.00
                    else addon_set_item.qty,
                    round(
                        addon.base_price * addon_set_item.qty
                        + addon.price_per_hour
                        * addon_set_item.qty
                        * decimal.Decimal(time_rented / timezone.timedelta(hours=1)),
                        2,
                    ),
                    True,
                ]
        for fee in self.added_context["estimate"].fees.all():
            self.added_context["fees"][fee] = [
                fee,
                fee.amount
                if fee.amount
                else round(
                    self.added_context["estimate"].subtotal * (fee.percentage / 100), 2
                ),
            ]
        for fee in self.added_context["estimate"].onetimefee_set.all():
            self.added_context["fees"][fee] = [
                fee,
                fee.amount
                if fee.amount
                else round(
                    self.added_context["estimate"].subtotal * (fee.percentage / 100), 2
                ),
            ]
        return super().dispatch(request, *args, **kwargs)


class viewInvoice(SLUGSMixin, TemplateView):
    template_name = "finance/invoice.html"
    added_context = {}

    def dispatch(self, request, *args, **kwargs):
        self.added_context = {
            "systems": {},
            "fees": {},
            "payments": {},
            "payment_amt": 0.00,
        }
        self.added_context["estimate"] = Estimate.objects.get(pk=kwargs["e_id"])
        self.added_context["shop_time"] = (
            self.added_context["estimate"]
            .gig.loadin_set.order_by("shop_time")
            .first()
            .shop_time
        )
        self.added_context["load_in"] = (
            self.added_context["estimate"]
            .gig.loadin_set.order_by("shop_time")
            .first()
            .load_in
        )
        self.added_context["load_out"] = (
            self.added_context["estimate"]
            .gig.loadin_set.order_by("-load_out")
            .first()
            .load_out
        )

        for system in self.added_context["estimate"].gig.systems.all():
            dept = system.department
            rented_start = (
                self.added_context["estimate"]
                .gig.loadin_set.filter(department=dept)
                .order_by("shop_time")
                .first()
                .shop_time
            )
            rented_end = (
                self.added_context["estimate"]
                .gig.loadin_set.filter(department=dept)
                .order_by("-load_out")
                .first()
                .load_out
            )
            time_rented = rented_end - rented_start
            self.added_context["systems"][system] = [
                system,
                decimal.Decimal(time_rented / timezone.timedelta(hours=1)),
                decimal.Decimal(time_rented / timezone.timedelta(hours=1))
                if system.price_per_hour
                else 1,
                round(
                    system.base_price
                    + system.price_per_hour
                    * decimal.Decimal(time_rented / timezone.timedelta(hours=1)),
                    2,
                ),
                False,
            ]
            addons = SystemInstance.objects.get(
                gig=self.added_context["estimate"].gig, system=system
            ).addoninstance_set.all()
            for addon_set_item in addons:
                addon = addon_set_item.addon
                self.added_context["systems"][addon_set_item.pk] = [
                    addon,
                    decimal.Decimal(time_rented / timezone.timedelta(hours=1)),
                    (
                        addon_set_item.qty
                        * decimal.Decimal(time_rented / timezone.timedelta(hours=1))
                    )
                    if addon.price_per_hour != 0.00
                    else addon_set_item.qty,
                    round(
                        addon.base_price * addon_set_item.qty
                        + addon.price_per_hour
                        * addon_set_item.qty
                        * decimal.Decimal(time_rented / timezone.timedelta(hours=1)),
                        2,
                    ),
                    True,
                ]
        for fee in self.added_context["estimate"].fees.all():
            self.added_context["fees"][fee] = [
                fee,
                fee.amount
                if fee.amount
                else round(
                    self.added_context["estimate"].subtotal * (fee.percentage / 100), 2
                ),
            ]
        for fee in self.added_context["estimate"].onetimefee_set.all():
            self.added_context["fees"][fee] = [
                fee,
                fee.amount
                if fee.amount
                else round(
                    self.added_context["estimate"].subtotal * (fee.percentage / 100), 2
                ),
            ]
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
                    time_in__range=(day, day + timezone.timedelta(days=1))
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
                time_in__range=(day, day + timezone.timedelta(days=1))
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
        pay_period = PayPeriod.objects.get(pk=kwargs["pp_id"])
        rates = {}
        for rate in Wage.objects.all().order_by("hourly_rate"):
            rates[rate] = [rate, 0]
        employees = {}
        for employee in Employee.objects.all().filter(is_active=True):
            employees[employee.bnum] = {
                "bnum": employee.bnum,
                "name": f"{employee.first_name} {employee.last_name}",
                "shifts": [],
                "rates": deepcopy(rates),
                "total_amount": 0.00,
            }
        for shift in pay_period.shifts.all():
            if shift.processed:
                # print(employees[shift.content_object.employee.bnum])
                print("\n\n\n")
                employees[shift.content_object.employee.bnum]["shifts"].append(shift)
                employees[shift.content_object.employee.bnum]["rates"][
                    shift.content_object.position.hourly_rate
                ][1] += (round(shift.total_time / timezone.timedelta(minutes=15)) / 4)
                employees[shift.content_object.employee.bnum]["total_amount"] += float(
                    shift.content_object.position.hourly_rate.hourly_rate
                ) * (round(shift.total_time / timezone.timedelta(minutes=15)) / 4)

        self.added_context["rates"] = rates
        self.added_context["employees"] = employees
        self.added_context["pay_period"] = pay_period

        print(employees)

        return super().dispatch(request, *args, **kwargs)


class EstimateDownload(SLUGSMixin, View):
    def get(self, request, relative_path):
        path = f"estimates/{relative_path}"
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
