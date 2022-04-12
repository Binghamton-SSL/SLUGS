from django_unicorn.components import UnicornView
from finance.models import Shift
from utils.generic_email import send_generic_email


class FinanceshiftView(UnicornView):
    shift: Shift = None
    has_parent = False

    def updated_search(self, query):
        self.parent.load_table()

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.has_parent = True if self.parent is not None else False
        self.shift = Shift.objects.get(pk=kwargs["shift"].pk)

    def accept(self):
        shift = Shift.objects.get(pk=self.shift.pk)
        shift.processed = False if shift.processed else True
        if shift.processed:
            shift.contested = False
        shift.save()
        self.shift = shift

    def contest(self):
        shift = Shift.objects.get(pk=self.shift.pk)
        shift.contested = False if shift.contested else True
        if shift.contested:
            shift.processed = False
        shift.save()
        self.shift = shift
        if shift.contested:
            # Sometimes we don't have an employee bc user error 
            try:
                send_generic_email(
                    request=None,
                    title="Your shift has been contested",
                    included_text=f"""
    Hey there {(shift.content_object.employee.preferred_name if shift.content_object.employee.preferred_name else shift.content_object.employee.first_name)},
    <br><br>
    Our Financial Director was looking over our records so we can pay you (yay!) but unfortunately it seems like there may have been an error made when you clocked in/out. Please reach out to the FD (bssl.finance@binghamtonsa.org) ASAP so that we can resolve this and get you paid!
    """,  # noqa
                    subject=f"[ACTION REQUIRED] Your shift has been contested",
                    to=[shift.content_object.employee.email],
                )
            except Exception:
                pass

    def delete(self):
        shift = Shift.objects.get(pk=self.shift.pk)
        shift.delete()
