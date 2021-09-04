from django.contrib.auth.models import Group
from django_unicorn.components import UnicornView
from gig.models import Gig, JobInterest, Job, DEPARTMENTS
from employee.models import Employee
from SLUGS.templatetags.grouping import has_group


class GigsignupView(UnicornView):
    jobs = {}
    all_jobs = {}
    user_id = None
    gig_id = None
    args = None
    kwargs = None

    def setJobs(self):
        self.jobs = {}
        gig = Gig.objects.get(pk=self.gig_id)
        user = Employee.objects.get(pk=self.user_id)
        probie_positions = Group.objects.filter(name__icontains="Probie")
        is_probie = (
            user.groups.all()
            .filter(name__in=[g.name for g in probie_positions])
            .exists()
        )
        depts = []
        for dept in DEPARTMENTS:
            if has_group(user, dept[1]):
                depts.append(dept[0])
        jobset = (
            gig.job_set.filter(employee=None, department__in=depts).exclude(
                position__in=probie_positions
            )
            if not is_probie
            else gig.job_set.filter(
                employee=None, department__in=depts, position__in=probie_positions
            )
        )
        for job in jobset:
            self.jobs[str(job.pk)] = [
                job,
                JobInterest.objects.filter(employee=user, job=job).first(),
                True,
            ]
            # Must test for job
            if job.position not in user.groups.all() and job.department in depts:
                self.jobs[str(job.pk)][2] = False
        # All jobs
        self.all_jobs = {}
        for job in gig.job_set.all():
            self.all_jobs[str(job.pk)] = job.position

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = kwargs["u_id"]
        self.gig_id = kwargs["gig_id"]
        self.setJobs()
        self.args = args
        self.kwargs = kwargs

    def mount(self):
        self.__init__(*self.args, **self.kwargs)

    def toggleInterest(self, job_id):
        job = Job.objects.get(pk=job_id)
        employee = Employee.objects.get(pk=self.user_id)
        is_Signedup = (
            True
            if JobInterest.objects.filter(employee=employee, job=job).first()
            is not None
            else False
        )
        if is_Signedup:
            JobInterest.objects.get(employee=employee, job=job).delete()
        else:
            JobInterest.objects.get_or_create(employee=employee, job=job)
        self.setJobs()
