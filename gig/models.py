from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse
from tinymce.models import HTMLField
from django.contrib.auth.models import Group

import client.models as client
import location.models as location
import employee.models as employee

DEPARTMENTS = [
    ("L", "Lighting"),
    ("S", "Sound"),
    ("M", "Manager"),
    ("O", "Other"),
    ("T", "Staging"),
]


class Gig(models.Model):
    """
    A BSSL Show.
    """
    name = models.CharField(max_length=200)
    notes = HTMLField(
        blank=True,
        null=True,
        help_text="This will show up on the showview page and the estimate as 'ATTN ENG'",
    )
    manager_only_notes = HTMLField(blank=True, null=True)
    setup_by = models.DateTimeField(verbose_name="Setup By")
    start = models.DateTimeField(verbose_name="Gig start time")
    end = models.DateTimeField(verbose_name="Gig end time")
    org = models.ForeignKey(client.Organization, models.PROTECT)
    contact = models.ForeignKey(client.OrgContact, models.PROTECT, null=True)
    location = models.ForeignKey(location.Location, models.PROTECT)
    day_of_show_notes = models.TextField(blank=True)
    archived = models.BooleanField(default=False)
    published = models.BooleanField(default=False)
    available_for_signup = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date Available for Signup",
        help_text="If left blank, this value will be set to 7 days prior to the start date.",
    )
    systems = models.ManyToManyField("equipment.System", through="SystemInstance")

    def get_staff_link(self):
        return format_html(
            "<a href='%s'>%s</a>"
            % (reverse("admin:gig_gig_staff", args=(self.id,)), "Staff Show")
        )

    def send_staffing_email(self):
        return format_html(
            "<a href='%s'>%s</a>"
            % (reverse("admin:gig_gig_email", args=(self.id,)), "Send staffing email")
        )

    def __str__(self):
        return (
            self.name
            + " - "
            + str(self.org)
            + " - "
            + str(timezone.localtime(self.start).strftime("%m/%d/%Y"))
            + (" [UNPUBLISHED]" if not self.published else "")
            + (" [ARCHIVED]" if self.archived else "")
        )  # noop

    def save(self, *args, **kwargs):
        if self.available_for_signup is None:
            self.available_for_signup = self.start - timezone.timedelta(days=7)
        super().save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super(Gig, self).__init__(*args, **kwargs)
        self.__loadin_depts__ = []


class LoadIn(models.Model):
    """
    A Load in for a show. Contains: the time employees should report to the shop (Shop Time), the time BSSL is to arrive at the venue (Load in time) and the time BSSL is to be done unpacking and go home (Load out time).
    """
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE)
    department = models.CharField(choices=DEPARTMENTS, max_length=1)
    note = models.CharField(max_length=128, blank=True, null=True, help_text="Use this only when further explaintation is needed as to which shift this loadin is for.")
    shop_time = models.DateTimeField()
    load_in = models.DateTimeField()
    load_out = models.DateTimeField()

    def __str__(self):
        return f"{self.department} - {self.gig}"


class SystemInstance(models.Model):
    """
    An instance of a :model:`equipment.System` applied to a :model:`gig.Gig`. Contains the addons and employees for this show.
    """
    system = models.ForeignKey("equipment.System", on_delete=models.PROTECT)
    addons = models.ManyToManyField(
        "equipment.SystemAddon", through="gig.AddonInstance", blank=True
    )
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE)
    employees = models.ManyToManyField(employee.Employee, through="Job")

    class Meta:
        verbose_name = "Rented System"
        verbose_name_plural = "Rented Systems"

    def __str__(self):
        return f"{self.system}"


class AddonInstance(models.Model):
    """
    An instance of a :model:`equipment.SystemAddon` applied to a :model:`gig.Gig`. Contains the addons and employees for this show.
    """
    addon = models.ForeignKey("equipment.SystemAddon", on_delete=models.CASCADE)
    systemInstance = models.ForeignKey("gig.SystemInstance", on_delete=models.CASCADE)
    description = models.CharField(max_length=200, blank=True, null=True)
    qty = models.IntegerField(default=1)

    class Meta:
        verbose_name = "Addon"
        verbose_name_plural = "Addons"


class Job(models.Model):
    """
    A Job that must be worked as part of a :model:`gig.Gig`.
    """
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE)
    employee = models.ForeignKey(
        employee.Employee, on_delete=models.SET_NULL, null=True, blank=True
    )
    position = models.ForeignKey(Group, on_delete=models.PROTECT)
    linked_system = models.ForeignKey(
        SystemInstance, on_delete=models.PROTECT, null=True, blank=True
    )
    department = models.CharField(choices=DEPARTMENTS, max_length=1)
    is_test = models.BooleanField(default=False)
    shifts = GenericRelation("finance.Shift")

    def __str__(self):
        return f"{self.gig.name} - {self.gig.org}"


class JobInterest(models.Model):
    """
    Interest from an employee to work a :model:`gig.Job`.
    """
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    employee = models.ForeignKey(employee.Employee, on_delete=models.CASCADE)
    submitted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee} - {self.job.gig}"
