from django_unicorn.components import UnicornView
from finance.models import Shift


class FinanceapproveallshiftsView(UnicornView):
    shifts = None
    allAccepted = False


    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.shifts = kwargs["shiftset"]
        # self.allAccepted =  self.shfits.filter(processed=False).count() == 0

    def acceptAll():
        for shift in self.shifts:
            shift.processed = True if not self.allAccepted else False
            shift.save()
        self.allAccepted = True if self.allAccepted == False else False