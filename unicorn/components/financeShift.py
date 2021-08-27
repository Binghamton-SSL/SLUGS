from django_unicorn.components import UnicornView
from finance.models import Shift


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

    def delete(self):
        shift = Shift.objects.get(pk=self.shift.pk)
        shift.delete()
