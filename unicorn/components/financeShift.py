from django_unicorn.components import UnicornView
from finance.models import Shift
from utils.generic_email import send_generic_email
import django.utils.timezone as timezone


class FinanceshiftView(UnicornView):
    shift: Shift = None
    has_parent = False
    can_be_contested = False

    def updated_search(self, query):
        self.parent.load_table()

    def updated(self, name, value):
        if (name == "shift.reason_contested"):
            shift = Shift.objects.get(pk=self.shift.pk)
            if len(value) == 0:
                shift.contested = False
                shift.reason_contested = None
                shift.save()
                self.can_be_contested = False
                self.shift = shift
            elif len(value) > 0:
                self.can_be_contested = True
                reason = self.shift.reason_contested
                self.shift = shift
                self.shift.reason_contested = reason
        super().updated(name, value)

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.has_parent = True if self.parent is not None else False
        if "shift" in kwargs:
            self.shift = Shift.objects.get(pk=kwargs["shift"].pk)
            if self.shift.reason_contested is not None:
                self.can_be_contested = True

    def accept(self):
        shift = Shift.objects.get(pk=self.shift.pk)
        shift.processed = False if shift.processed else True
        if shift.processed:
            shift.contested = False
        shift.save()
        self.shift = shift

    def contest(self):
        reason = self.shift.reason_contested
        shift = Shift.objects.get(pk=self.shift.pk)
        if shift.contested:
            shift.contested = False
            shift.reason_contested = None
            self.can_be_contested = False
        else:
            shift.contested = True
            shift.processed = False
            shift.reason_contested = reason
        shift.save()
        self.shift = shift
        if shift.contested:
            # Sometimes we don't have an employee bc user error 
            try:
                send_generic_email(
                    request=None,
                    title="A shift of yours has been contested",
                    included_text=f"""
    Hey there {(shift.content_object.employee.preferred_name if shift.content_object.employee.preferred_name else shift.content_object.employee.first_name)},
    <br><br>
    Our Financial Director was looking over our records so we can pay you (yay!) but unfortunately it seems like there may have been an error made when you clocked in/out. <br/><br/> 
    {timezone.template_localtime(shift.time_in).strftime('%m/%d/%y %H:%M:%S')} - {timezone.template_localtime(shift.time_out).strftime('%m/%d/%y %H:%M:%S')} <b>{shift.content_object}</b> ({shift.total_time} - ${round(shift.cost, 2)})<br/><br/>
    <b>Reason Provided:</b> <code>{shift.reason_contested}</code> <br/><br/> Please reach out to the FD (bssl.finance@binghamtonsa.org) ASAP so that we can resolve this and get you paid!
    """,  # noqa
                    subject="[ACTION REQUIRED] Your shift has been contested",
                    to=[shift.content_object.employee.email],
                )
            except Exception:
                pass

    def delete(self):
        shift = Shift.objects.get(pk=self.shift.pk)
        shift.delete()
