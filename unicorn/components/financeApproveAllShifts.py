from django_unicorn.components import UnicornView
from finance.models import Shift
from django.core.exceptions import ValidationError


class FinanceapproveallshiftsView(UnicornView):
    shifts = None
    allAccepted = False

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        try:
            self.shifts = kwargs["shiftset"]
            self.allAccepted = kwargs["shiftset"].filter(processed=False).exclude(contested=True).count() == 0
        except KeyError:
            raise ValidationError({"allAccepted": "There was an error. Please contact the SLUGS administrator"}, code="invalid") 

    def acceptAll(self):
        for shift in self.shifts.exclude(contested=True):
            s = Shift.objects.get(pk=shift.pk)
            s.processed = True if not self.allAccepted else False
            try:
                s.save()
            except ValidationError:
                # TODO ideally we'd like to alert the user here when this happens
                pass
        self.allAccepted = True if self.allAccepted is False else False
