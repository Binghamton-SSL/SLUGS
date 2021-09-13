import django.utils.timezone as timezone
from django.db.models import Q
from django_unicorn.components import UnicornView
from employee.models import Employee


class WeekloginView(UnicornView):
    emps = Employee.objects.none()
    empsnopass = Employee.objects.none()
    sevendayago = timezone.now()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.emps = Employee.objects.filter(is_active=True)
        self.sevendayago = self.sevendayago - timezone.timedelta(days=7)
        self.empsnopass = self.emps.filter(Q(password='') | Q(password__isnull=True))
        self.emps = self.emps.filter(last_login__lte=self.sevendayago)
