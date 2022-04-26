from django import template
from django.utils import timezone
from gig.models import Gig, Job


register = template.Library()

@register.inclusion_tag("employee/components/id.html")
def id(user):
    next_job = (
        Job.objects.filter(employee=user)
        .filter(gig__end__gte=(timezone.now() + timezone.timedelta(hours=-5)))
        .order_by("gig__end")
    )
    gig_happening = False
    if len(next_job) > 0:
        next_gig = Gig.objects.get(pk=next_job.first().gig.pk)
        your_load_ins = next_gig.loadin_set.filter(
            department=next_job.first().department
        ).order_by("load_in")
        gig_happening = your_load_ins.first().shop_time < (
                timezone.now() + timezone.timedelta(minutes=10)
            ) and your_load_ins.last().load_out > (
                timezone.now() + timezone.timedelta(hours=-5)
            )
        your_depts = [d.get_department_display() for d in your_load_ins] + [" "]
        jobs_in_gig = Job.objects.filter(employee=user, gig=next_gig)
    return locals()