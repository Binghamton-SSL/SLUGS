from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import localtime, now
from django_unicorn.components import UnicornView
from finance.models import TimeSheet
from django.contrib.admin.models import LogEntry, CHANGE


class MarktimesheetsignedView(UnicornView):
    message = ""
    status = ""
    date = now().date()

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

    def updateTS(self, code, id):
        if code == 13:
            self.status = ""
            if id != "":
                try:
                    ts = TimeSheet.objects.get(pk=id)
                    ts.signed = self.date
                    ts.save()
                    LogEntry.objects.log_action(
                        user_id=self.request.user.pk if self.request else '',
                        content_type_id=ContentType.objects.get_for_model(
                            ts, for_concrete_model=False
                        ).pk,
                        object_id=ts.pk,
                        object_repr=str(ts),
                        action_flag=CHANGE,
                        change_message=f"Updated date signed to: {ts.signed} via mark time sheet as signed widget.",
                    )
                    self.message = f"Timesheet {id} Signed with date {self.date}"
                    self.status = "g"
                except TimeSheet.DoesNotExist:
                    if type(id) == int:
                        self.message = f"Timesheet {id} does not exist"
                        self.status = "b"
                    else:
                        self.message = "This timesheet ID doesn't seem right...."
                        self.status = "b"
                    
