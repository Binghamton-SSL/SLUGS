import re
from django.db import models
from django.urls import reverse
import django.utils.timezone as timezone
from tinymce.models import HTMLField
from django_ical.views import ICalFeed
from icalendar import vCalAddress, vText
from gig.models import Gig, Job
from employee.models import Employee
from django.contrib.auth.models import Group
from django.db.models import Q
from datetime import datetime


# Create your models here.
class Notification(models.Model):
    MESSAGE_TYPES = [
        ("normal bg-white text-black", "Normal"),
        ("bg-green-500", "Success"),
        ("bg-yellow-500", "Warning"),
        ("bg-red-500", "Danger/Error"),
    ]
    name = models.CharField(max_length=150)
    groups_to_send_to = models.ManyToManyField(
        Group,
        blank=True,
        help_text="Send the notification to the following groups.",
    )
    message = HTMLField()
    message_type = models.CharField(
        choices=MESSAGE_TYPES, max_length=64, default="normal"
    )
    date_published = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.date_published) + " - " + self.name


class signupStatus(models.Model):
    is_open = models.BooleanField()

    def __str__(self):
        return f'Signup is currently {"Open" if self.is_open else "Closed"}'


class onboardingStatus(models.Model):
    is_open = models.BooleanField()

    def __str__(self):
        return f'User onboarding is currently {"Open" if self.is_open else "Closed"}'


class ShowFeed(ICalFeed):
    product_id = "-//slugs.bssl.binghamtonsa.org//Shows//EN"
    title = "BSSL Event Calendar"
    description = "Events which are booked via S.L.U.G.S."
    file_name = "bssl_events.ics"
    hidetentative = True

    def items(self):
        return Gig.objects.filter(published=self.hidetentative).order_by(
            "-start"
        )  # noqa For now; only show published events

    def item_title(self, item):
        return f"{'[TENTATIVE] ' if not item.published else ''}{item.org} - {item.name}"

    def item_description(self, item):
        nl = "\n"
        return f"""
{"[TENTATIVE] " if not item.published else ""}{item.name}

Location: {item.location}
Organization: {item.org}
Contact: {item.contact.name}

Systems:
{''.join([f"{system.name} - {system.get_department_display()}{' + '+(' + '.join([addon.name for addon in system.systeminstance_set.get(gig=item.pk).addons.all()])) if len(system.systeminstance_set.get(gig=item.pk).addons.all()) else ''}{nl}" for system in item.systems.all()])}
Load in/out:
{''.join([f"{loadin.get_department_display()}:{nl}⇊ {(loadin.shop_time-timezone.timedelta(hours=4)).strftime('%m/%d/%Y, %H:%M:%S')}{nl}>> {(loadin.load_in-timezone.timedelta(hours=4)).strftime('%m/%d/%Y, %H:%M:%S')}{nl}<< {(loadin.load_out-timezone.timedelta(hours=4)).strftime('%m/%d/%Y, %H:%M:%S')}{nl}{nl}" for loadin in item.loadin_set.all()])}
Staff:
{''.join([f"{staff.department} - {staff.position}: {(staff.employee.preferred_name if staff.employee.preferred_name else staff.employee.first_name) if staff.employee is not None else 'TBA'} {staff.employee.last_name if staff.employee is not None else ''}{nl}" for staff in item.job_set.all().order_by('department')])}
        """  # noqa

    def item_link(self, item):
        return reverse("gig:showView", args=[item.pk])

    def item_location(self, item):
        return item.location

    def item_organizer(self, item):
        organizer = vCalAddress("MAILTO:bssl@binghamtonsa.org")
        organizer.params["cn"] = vText("Binghamton Sound Stage & Lighting")
        return organizer

    def item_attendee(self, item):
        attendees = []
        for job in item.job_set.all():
            if job.employee is not None:
                attendee = vCalAddress(f"MAILTO:{job.employee.email}")
                attendee.params["cn"] = vText(
                    f"{(job.employee.preferred_name if job.employee.preferred_name else job.employee.first_name)} {job.employee.last_name}"
                )
                attendees.append(attendee)
        return attendees

    def item_start_datetime(self, item):
        return item.start

    def item_end_datetime(self, item):
        return item.end

    def item_status(self, item):
        return "CONFIRMED" if item.published else "TENTATIVE"


class TentativeShowFeed(ShowFeed):
    product_id = "-//slugs.bssl.binghamtonsa.org//TentativeShows//EN"
    title = "BSSL Tentative Event Calendar"
    description = "Events which may be booked via S.L.U.G.S."
    file_name = "bssl_tenatitive_events.ics"
    hidetentative = False


class DeptFeed(ICalFeed):
    department = (None, None)

    def __init__(self):
        self.product_id = f"-//slugs.bssl.binghamtonsa.org//{self.department[1]}//EN"
        self.title = f"BSSL {self.department[1]} Work Calendar"
        self.description = (
            f"Events which are booked via S.L.U.G.S. - {self.department[1]} Work"
        )
        self.file_name = f"{self.department[1]}_work.ics"

    def items(self):
        return (
            Gig.objects.all()
            .filter(published=True)
            .filter(systems__department=self.department[0])
            .order_by("-start")
        )

    def item_title(self, item):
        return f"{'[TENTATIVE] ' if not item.published else ''}{item.org} - {item.name}"

    def item_description(self, item):
        nl = "\n"
        return f"""
{"[TENTATIVE] " if not item.published else ""}{item.name}

Location: {item.location}
Organization: {item.org}
Contact: {item.contact.name}

Systems:
{''.join([f"{system.name} - {system.get_department_display()}{' + '+(' + '.join([addon.name for addon in system.systeminstance_set.get(gig=item.pk).addons.all()])) if len(system.systeminstance_set.get(gig=item.pk).addons.all()) else ''}{nl}" for system in item.systems.filter(department=self.department[0])])}
Load in/out:
{''.join([f"{loadin.get_department_display()}:{nl}⇊ {(loadin.shop_time-timezone.timedelta(hours=4)).strftime('%m/%d/%Y, %H:%M:%S')}{nl}>> {(loadin.load_in-timezone.timedelta(hours=4)).strftime('%m/%d/%Y, %H:%M:%S')}{nl}<< {(loadin.load_out-timezone.timedelta(hours=4)).strftime('%m/%d/%Y, %H:%M:%S')}{nl}{nl}" for loadin in item.loadin_set.filter(department=self.department[0])])}
Staff:
{''.join([f"{staff.department} - {staff.position}: {(staff.employee.preferred_name if staff.employee.preferred_name else staff.employee.first_name) if staff.employee is not None else 'TBA'} {staff.employee.last_name if staff.employee is not None else ''}{nl}" for staff in item.job_set.filter(department=self.department[0]).order_by('department')])}
        """  # noqa

    def item_link(self, item):
        return reverse("gig:showView", args=[item.pk])

    def item_location(self, item):
        return item.location

    def item_organizer(self, item):
        organizer = vCalAddress("MAILTO:bssl@binghamtonsa.org")
        organizer.params["cn"] = vText("Binghamton Sound Stage & Lighting")
        return organizer

    def item_attendee(self, item):
        attendees = []
        for job in item.job_set.filter(department=self.department[0]):
            if job.employee is not None:
                attendee = vCalAddress(f"MAILTO:{job.employee.email}")
                attendee.params["cn"] = vText(
                    f"{(job.employee.preferred_name if job.employee.preferred_name else job.employee.first_name)} {job.employee.last_name}"
                )
                attendees.append(attendee)
        return attendees

    def item_start_datetime(self, item):
        return item.loadin_set.filter(department=self.department[0]).first().shop_time

    def item_end_datetime(self, item):
        return item.loadin_set.filter(department=self.department[0]).last().load_out

    def item_status(self, item):
        return "CONFIRMED" if item.published else "TENTATIVE"


class LightingFeed(DeptFeed):
    department = ("L", "Lighting")


class SoundFeed(DeptFeed):
    department = ("S", "Sound")


class StageFeed(DeptFeed):
    department = ("T", "Stage")


# Item Schema: 
# {
#     start: datetime,
#     end: datetime,
#     title: str,
#     description: str,
#     location: str,
#     link: str,
# }
class EmployeeFeed(ICalFeed):
    employee = None

    def get_object(self, request, *args, **kwargs):
        return int(kwargs['emp_id'])

    def __init__(self):
        self.product_id = "-//slugs.bssl.binghamtonsa.org//SHIFT_CAL//EN"
        self.title = "BSSL Work Calendar"
        self.description = "Shifts you work for BSSL"
        self.file_name = "BSSL_shifts.ics"

    def items(self, emp_id):
        # TODO - Add trainings
        self.employee = Employee.objects.get(pk=emp_id)
        items = []
        jobs = (
            Job.objects.filter(employee=self.employee)
        )
        for job in jobs.all():
            gig = Gig.objects.get(pk=job.gig.pk)
            your_load_ins = gig.loadin_set.filter(
                department=job.department
            ).order_by("load_in")
            for load_in in your_load_ins.all():
                items.append({
                    "start": load_in.load_in,
                    "end": load_in.load_out,
                    "title": f"{gig.org} - {gig.name}",
                    "description": "",
                    "location": gig.location,
                    "link": reverse("gig:showView", args=[gig.pk]),
                })
            items.append({
                "start": gig.setup_by,
                "end": gig.setup_by,
                "title": f"SETUP BY TIME: {gig.org} - {gig.name}",
                "description": "",
                "location": gig.location,
                "link": reverse("gig:showView", args=[gig.pk]),
            })
            items.append({
                "start": gig.start,
                "end": gig.end,
                "title": f"SHOW: {gig.org} - {gig.name}",
                "description": re.sub('<[^<]+?>', '', gig.notes),
                "location": gig.location,
                "link": reverse("gig:showView", args=[gig.pk]),
            })
        return items

    def item_title(self, item):
        return item["title"]

    def item_description(self, item):
        return item["description"]

    def item_guid(self, item):
        return f'{self.product_id}-{item["title"]}-{item["start"]}-{item["link"]}'

    def item_link(self, item):
        return item["link"]

    def item_location(self, item):
        return item["location"]

    def item_organizer(self, item):
        organizer = vCalAddress("MAILTO:bssl@binghamtonsa.org")
        organizer.params["cn"] = vText("Binghamton Sound Stage & Lighting")
        return organizer

    def item_start_datetime(self, item):
        return item["start"]

    def item_end_datetime(self, item):
        return item["end"]

    def item_status(self, item):
        return "CONFIRMED"


class PricingMixin:
    pricing_set = None

    def get_current_price(self):
        return self.pricing_set.filter(
            Q(date_active__lte=datetime.now())
            &
            (
                Q(date_inactive__gt=datetime.now())
                |
                Q(date_inactive=None)
            )
        ).first()

    def get_is_active(self):
        return True if self.get_current_price() is not None else False

    def get_price_at_date(self, date):
        return self.pricing_set.filter(
            Q(date_active__lte=date)
            &
            (
                Q(date_inactive__gte=date)
                |
                Q(date_inactive=None)
            )
        ).first()
