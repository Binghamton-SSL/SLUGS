from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.auth.models import Group
from gig.models import DEPARTMENTS
from tinymce.models import HTMLField
from django.utils import timezone


# Create your models here.
class Training(models.Model):
    date = models.DateTimeField()
    dept = models.CharField(max_length=1, choices=DEPARTMENTS)
    location = models.ForeignKey(
        "location.Location", on_delete=models.SET_NULL, null=True, blank=True
    )
    capacity = models.IntegerField(null=True, blank=True)
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
        return f"{self.get_dept_display()} Training - {self.date.strftime('%m/%d/%Y, %H:%M:%S')}"


class Trainee(models.Model):
    employee = models.ForeignKey("employee.Employee", on_delete=models.CASCADE)
    training = models.ForeignKey("training.Training", on_delete=models.CASCADE)
    position = models.ForeignKey(
        Group, default="New Hire", to_field="name", on_delete=models.PROTECT
    )
    shifts = GenericRelation("finance.Shift")

    def __str__(self):
        return f"{self.training}"


class TrainingRequest(models.Model):
    employee = models.ForeignKey("employee.Employee", on_delete=models.CASCADE)
    systems = models.ManyToManyField("equipment.System", blank=True)
    notes = models.TextField(null=True, blank=True)
    submitted = models.DateTimeField(auto_now_add=True)
    answered = models.BooleanField(default=False)

    def __str__(self):
        return f'{"[ANSWERED] " if self.answered else ""}{self.employee} - {timezone.localtime(self.submitted).strftime("%a, %d %b %Y %H:%M:%S %Z")}'
