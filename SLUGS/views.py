from django.shortcuts import render, redirect
from django.urls import reverse
from gig.models import Employee, Signup
from employee.models import Notification
from datetime import datetime

def index(request):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % (reverse('auth:login'), request.path))
    gigs = Employee.objects.filter(linked_employee=request.user,not_associated_with_event=False).values('linked_gig__name','linked_gig__start','linked_gig__end','linked_gig__org__name','linked_gig__location__name','linked_gig__id').order_by('-linked_gig__start')[:5]
    nextGig = Employee.objects.filter(linked_employee=request.user).filter(linked_gig__start__gte=datetime.now()).values('linked_gig__name','linked_gig__start','linked_gig__end','linked_gig__org__name','linked_gig__location__name','linked_gig__id').order_by('linked_gig__start')[:1]
    signup = Signup.objects.get(id=1).is_open
    notifications = Notification.objects.all().filter()
    return render(request, 'index.html',{'user': request.user, 'gigs': gigs, 'nextGig': nextGig, 'signup_open': signup, "notifications": notifications})