from django import template


register = template.Library()


@register.inclusion_tag("gig/components/ticket.html")
def ticket(gig):
    return locals()


@register.filter
def duration(td):
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    return "{} hours {} min".format(hours, minutes)
