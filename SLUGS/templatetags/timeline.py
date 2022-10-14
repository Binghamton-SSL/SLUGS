from django import template
from django.utils import timezone
from gig.models import Gig, Job

register = template.Library()


@register.inclusion_tag("components/timeline.html")
def timeline(emp):
    next_job = (
        Job.objects.filter(employee=emp)
        .filter(gig__end__gte=(timezone.now() + timezone.timedelta(hours=-5)))
        .order_by("gig__end")
    )
    if len(next_job) > 0:
        next_gig = Gig.objects.get(pk=next_job.first().gig.pk)
        your_load_ins = next_gig.loadin_set.filter(
            department=next_job.first().department
        ).order_by("load_in")
        load_in_info = [
            {
                "loadin": load_in,
                "relative_start": (
                    load_in.load_in - next_gig.loadin_set.first().load_in
                )
                / timezone.timedelta(minutes=15),
                "realtive_end": (load_in.load_out - load_in.load_in)
                / timezone.timedelta(minutes=15),
            }
            for load_in in your_load_ins
        ]
        gig_happening = your_load_ins.first().shop_time < (
            timezone.now() + timezone.timedelta(minutes=10)
        ) and your_load_ins.last().load_out > (
            timezone.now() + timezone.timedelta(hours=-5)
        )
        your_depts = list(set([d.get_department_display() for d in your_load_ins] + [" "]))
        events = [
            {
                "content": f'{next_gig.name} <br><sub>{timezone.template_localtime(next_gig.start).strftime("%H:%M")}-{timezone.template_localtime(next_gig.end).strftime("%H:%M")}</sub>',
                "start": timezone.template_localtime(next_gig.start).strftime(
                    "%m/%d/%Y, %H:%M:%S"
                ),
                "end": timezone.template_localtime(next_gig.end).strftime(
                    "%m/%d/%Y, %H:%M:%S"
                ),
                "group": len(your_depts) - 1,
            },
            {
                "content": f'Setup-by Time <br><sub>{timezone.template_localtime(next_gig.setup_by).strftime("%H:%M")}</sub>',
                "start": timezone.template_localtime(next_gig.setup_by).strftime(
                    "%m/%d/%Y, %H:%M:%S"
                ),
                "group": len(your_depts) - 1,
                "style": "background-color: #F87171!important",
            },
        ]
        for load_in in your_load_ins:
            group = your_depts.index(load_in.get_department_display())
            events.extend(
                [
                    {
                        "content": f'Shop Time <br><sub>{timezone.template_localtime(load_in.shop_time).strftime("%H:%M")}</sub>',
                        "start": timezone.template_localtime(
                            load_in.shop_time
                        ).strftime("%m/%d/%Y, %H:%M:%S"),
                        "group": group,
                    },
                    {
                        "content": f'Load in <br><sub>{timezone.template_localtime(load_in.load_in).strftime("%H:%M")}</sub>',
                        "start": timezone.template_localtime(load_in.load_in).strftime(
                            "%m/%d/%Y, %H:%M:%S"
                        ),
                        "group": group,
                    },
                    {
                        "content": f'Load out <br><sub>{timezone.template_localtime(load_in.load_out).strftime("%H:%M")}</sub>',
                        "start": timezone.template_localtime(load_in.load_out).strftime(
                            "%m/%d/%Y, %H:%M:%S"
                        ),
                        "group": group,
                    },
                ]
            )
    return locals()
