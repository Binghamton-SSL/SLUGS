from django import template
from django.utils import timezone
from gig.models import Gig, Job

register = template.Library()

@register.inclusion_tag('components/timeline.html')
def timeline(emp):
    next_job = Job.objects.filter(employee=emp).filter(gig__end__gte=(timezone.now() + timezone.timedelta(hours=-5))).order_by("gig__end")[:1]
    if len(next_job) > 0:
        next_gig = Gig.objects.get(pk=next_job.first().gig.pk)
        hours_in_gig = (next_gig.loadin_set.last().load_out - next_gig.loadin_set.first().load_in) / timezone.timedelta(hours=1)
        your_load_ins = next_gig.loadin_set.filter(department=next_job.first().department).order_by('load_in')
        load_in_info = [{"loadin": load_in, "relative_start": (load_in.load_in - next_gig.loadin_set.first().load_in) / timezone.timedelta(minutes=15), "realtive_end": (load_in.load_out - load_in.load_in) / timezone.timedelta(minutes=15)} for load_in in your_load_ins]
        gig_happening = your_load_ins.first().shop_time < ( timezone.now() + timezone.timedelta(hours=5) )  and your_load_ins.last().load_out > ( timezone.now() + timezone.timedelta(hours=-5) )
    return locals()
