from functools import reduce
from django.db.models import Q
from finance.models import HourlyRate
from django.utils import timezone


def cost_of_shifts(shifts):
    return round(
        float(
            reduce(
                lambda sum, shift: (
                    sum
                    + float(
                        HourlyRate.objects.get(
                            Q(wage=shift.content_object.position.hourly_rate)
                            & Q(date_active__lte=shift.time_in)
                            & (
                                Q(date_inactive__gt=shift.time_in)
                                | Q(date_inactive=None)
                            )
                        ).hourly_rate
                    )
                    * (round(shift.total_time / timezone.timedelta(minutes=15)) / 4)
                ),
                shifts,
                0,
            )
        ),
        2,
    )
