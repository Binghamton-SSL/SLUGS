from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.auth.models import Group
from gig.models import DEPARTMENTS
from tinymce.models import HTMLField
from django.utils import timezone


# Create your models here.
class Training(models.Model):
    """
    A training conducted by Managerial staff for employees.
    """
    date = models.DateTimeField()
    dept = models.CharField(max_length=1, choices=DEPARTMENTS)
    location = models.ForeignKey(
        "location.Location", on_delete=models.SET_NULL, null=True, blank=True
    )
    capacity = models.IntegerField(null=True, blank=True, help_text="Number of people allowed to sign up for this training including all trainers")
    paid = models.BooleanField(default=False, help_text="Allows employees to clock in using the SLUGS kiosk to get paid for this training")
    trainers = models.ManyToManyField("employee.Employee", related_name="trainers")
    attendees = models.ManyToManyField(
        "employee.Employee",
        through="training.Trainee",
        related_name="attendees",
        blank=True,
    )
    notes = HTMLField(null=True, blank=True)
    systems = models.ManyToManyField("equipment.System", blank=True)

    def __str__(self):
        return f"{self.get_dept_display()} Training"


class Trainee(models.Model):
    """
    An employee who participates in a training. Position defaults to New Hire
    """
    employee = models.ForeignKey("employee.Employee", on_delete=models.CASCADE)
    training = models.ForeignKey("training.Training", on_delete=models.CASCADE)
    override_allow_paid = models.BooleanField(default=False)
    position = models.ForeignKey(
        Group, default="Trainee", to_field="name", on_delete=models.PROTECT
    )
    shifts = GenericRelation("finance.Shift", related_query_name="trainee")

    def __str__(self):
        return f"{self.training}"


class TrainingRequest(models.Model):
    """
    A request from an employee for Training on a particular system
    """
    employee = models.ForeignKey("employee.Employee", on_delete=models.CASCADE)
    systems = models.ManyToManyField("equipment.System", blank=True)
    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Be sure to include when you're free in the upcoming weeks to schedule the training",
    )
    submitted = models.DateTimeField(auto_now_add=True)
    answered = models.BooleanField(default=False)

    def __str__(self):
        return f'{"[ANSWERED] " if self.answered else ""}{self.employee} - {timezone.localtime(self.submitted).strftime("%a, %d %b %Y %H:%M:%S %Z")}'
