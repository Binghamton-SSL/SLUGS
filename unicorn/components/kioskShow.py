from django_unicorn.components import UnicornView

from gig.models import Gig, Job
from finance.models import Shift
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


class KioskshowView(UnicornView):
    ongoing_shows = None
    show_error_message = None
    show_shown = []
    job_content_type = ContentType.objects.get(model="job").id
    last_show_update = timezone.now()

    def toggle_modal(self, gig_id):
        if gig_id in self.show_shown:
            self.show_shown.remove(gig_id)
        else:
            self.show_shown.append(gig_id)
        self.update_gig_status()

    def toggle_clock(self, job_id):
        job = Job.objects.get(pk=job_id)
        employee_shifts = Shift.objects.filter(
                    object_id=job.id,
                    content_type_id=self.job_content_type,
                    time_out=None
                )
        clocked_in = employee_shifts.order_by('time_in').last() if employee_shifts.count() > 0 else None
        if(clocked_in):
            clocked_in.time_out = timezone.now()
            clocked_in.save()
            job.save()
        else:
            job.shifts.create(time_in=timezone.now())
            job.save()
        self.update_gig_status()

    def update_gig_status(self):
        self.ongoing_shows = [{"gig": gig, "jobs": {}, "shown": True if gig.pk in self.show_shown else False} for gig in Gig.objects.filter(published=True, archived=False, start__lte=(timezone.now() + timezone.timedelta(hours=+29)), start__gte=(timezone.now() + timezone.timedelta(hours=-29)))]
        for show in self.ongoing_shows:
            gig = show["gig"]
            for job in Job.objects.filter(gig=gig.pk):
                # Are they currently clocked in?
                employee_shifts = Shift.objects.filter(
                    object_id=job.id,
                    content_type_id=self.job_content_type,
                    time_out=None
                )
                clocked_in = employee_shifts.order_by('time_in').last() if employee_shifts.count() > 0 else None

                if job.get_department_display() not in show['jobs']:
                    show['jobs'][job.get_department_display()] = {}
                if job.position.name not in show['jobs'][job.get_department_display()]:
                    show['jobs'][job.get_department_display()][job.position.name] = []
                show['jobs'][job.get_department_display()][job.position.name].append([job, clocked_in])
        self.last_show_update = timezone.now()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_gig_status()
