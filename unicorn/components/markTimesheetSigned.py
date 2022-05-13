from django.utils.timezone import localtime, now
from django_unicorn.components import UnicornView
from finance.models import TimeSheet


class MarktimesheetsignedView(UnicornView):
    message = ""
    status = ""
    date = now().date()

    def updateTS(self, code, id):
        if code == 13:
            self.status = ""
            if id is not "":
                try:
                    ts = TimeSheet.objects.get(pk=id)
                    ts.signed = self.date
                    ts.save()
                    self.message = f"Timesheet {id} Signed with date {self.date}"
                    self.status = "g"
                except TimeSheet.DoesNotExist:
                    if type(id) == int:
                        self.message = f"Timesheet {id} does not exist"
                        self.status = "b"
                    else:
                        self.message = "This timesheet ID doesn't seem right...."
                        self.status = "b"
                    
