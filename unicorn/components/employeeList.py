from django_unicorn.components import UnicornView
from gig.models import Job, Gig


class EmployeelistView(UnicornView):
    show_id = None
    my_job = None
    selectedDept = None
    depts = None
    jobs = None

    def choose_dept(self, dept):
        self.selectedDept = dept
        self.jobs = Job.objects.filter(gig=self.show_id, department=self.selectedDept)

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.show_id = kwargs.get("show")
        self.my_job = kwargs.get("my_job")
        if self.show_id is not None:
            gig = Gig.objects.get(pk=self.show_id)
            self.depts = list(
                set(
                    [
                        (dept.department, dept.get_department_display())
                        for dept in gig.job_set.all()
                    ]
                )
            )
            self.selectedDept = self.depts[0][0] if len(self.depts) > 0 else None
            self.jobs = Job.objects.filter(gig=self.show_id, department=self.selectedDept)
