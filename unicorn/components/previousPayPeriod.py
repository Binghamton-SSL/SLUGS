from django_unicorn.components import UnicornView
from django.db.models import Q
from django.db.models import Sum
import django.utils.timezone as timezone
from finance.models import Shift, PayPeriod


class PreviouspayperiodView(UnicornView):
    sub_shifts = None
    sub_pay_period = None
    selected_pp = None
    available_pay_period = None
    sub_shifts_hours = None
    sub_shifts_price = None

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.available_pay_period = PayPeriod.objects.all().order_by("-end")

    def updated(self, name, value):
        super().updated(name, value)
        if self.selected_pp != "-1":
            self.sub_pay_period = PayPeriod.objects.get(pk=self.selected_pp)
            self.sub_shifts = Shift.objects.filter(
                Q(time_in__gte=self.sub_pay_period.start)
                & Q(time_out__lte=self.sub_pay_period.end + timezone.timedelta(days=1))
            ).order_by("-time_out")
            self.sub_shifts_hours = str(self.sub_shifts.aggregate(Sum('total_time'))['total_time__sum'])
            self.sub_shifts_price = self.sub_shifts.aggregate(Sum("cost"))
        else:
            self.sub_pay_period = None
            self.sub_shifts = None
