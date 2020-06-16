from django.db import models

from gig.models import System
from employee.models import Employee

# Create your models here.
class TrainingRequest(models.Model):
    training_datetime = models.DateTimeField(null=True)
    system = models.ForeignKey(System, models.PROTECT)

class Trainee(models.Model):
    linked_employee = models.ForeignKey(Employee, models.PROTECT)

class Trainer(models.Model):
    linked_employee = models.ForeignKey(Employee, models.PROTECT)