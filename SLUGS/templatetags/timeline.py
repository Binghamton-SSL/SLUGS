from django import template
from gig.models import Gig

register = template.Library()

# @register.inclusion_tag('components/timeline.html')
# def timeline(emp):
#     Job.objects.filter(employee=emp)
#                 .filter(gig__end__gte=(timezone.now() + timezone.timedelta(hours=5)))
#                 .values(
#                     "gig__id",
#                 )
#                 .order_by("gig__end")[:1]
#     emp_current_gig = Gig.objects.filter() 
#     return {
#         "gig_happening": True
#     }