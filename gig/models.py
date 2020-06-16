from __future__ import print_function
from django.db import models
import employee.models as employeeModels
from django.contrib.auth.models import Group
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from phonenumber_field.modelfields import PhoneNumberField
from django.urls import reverse
from django.utils.html import format_html
from datetime import datetime

DEPARTMENTS = [
    ("L", 'Lighting'),
    ("S", 'Sound'),
    ("M", 'Manager'),
    ("O", 'Other'),
]

class Organization(models.Model):
    name = models.CharField(max_length=200)
    SA_account_num = models.BigIntegerField(null=True,blank=True)

    def __str__(self):
        return self.name

class Contact(models.Model):
    name = models.CharField(max_length=200)
    linked_org = models.ForeignKey(Organization,models.PROTECT)
    phone_number = PhoneNumberField(null=True,blank=True)
    email = models.EmailField(max_length=255,null=True,blank=True)

    def __str__(self):
        return self.name

class Location(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class System(models.Model):
    name = models.CharField(max_length=200)
    is_addon = models.BooleanField(default=False)
    department = models.CharField(max_length=1, choices=DEPARTMENTS)
    base_price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    def __str__(self):
        return self.department + " - " + self.name


class Gig(models.Model):
    # STATUS_TYPES = [
    #     ("T", 'Tentative'),
    #     ("C", 'Confirmed'),
    #     ("F", 'Finished'),
    # ]
    # status = models.CharField(choices=STATUS_TYPES,max_length=1, null=True, default='T')
    name = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    load_in_lighting = models.DateTimeField()
    load_in_sound = models.DateTimeField()
    start = models.DateTimeField(verbose_name='Gig start time')
    end = models.DateTimeField()
    load_out_lighting = models.DateTimeField()
    load_out_sound = models.DateTimeField()
    org = models.ForeignKey(Organization, models.PROTECT)
    contact = models.ForeignKey(Contact, models.PROTECT,null=True)
    location = models.ForeignKey(Location, models.PROTECT)
    day_of_show_notes = models.TextField(blank=True)
    archived = models.BooleanField(default=False)

    def get_assign_link(self):
        return format_html("<a href='%s'>%s</a>" % (reverse('admin:gig_gig_assign', args=(self.id,)), "Assign Staffing"))

    def __str__(self):
        return self.name + " - " + str(self.org) + " - " + str(self.start.date())

    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)

class Employee(models.Model):
    linked_employee = models.ForeignKey(employeeModels.Employee,models.PROTECT, blank=True, null=True)
    linked_gig = models.ForeignKey(Gig,models.CASCADE, blank=True, null=True)
    linked_system = models.ForeignKey(System,models.CASCADE, blank=True, null=True)
    employee_type = models.ForeignKey(Group,models.PROTECT)
    department = models.CharField(max_length=1, choices=DEPARTMENTS)
    not_associated_with_event = models.BooleanField(default=False)
    shift_objects = GenericRelation('Shift')

    def __str__(self):
        return self.department + " - " + self.linked_employee.__str__()
    class Meta:
        verbose_name = 'Hired Employee'
        verbose_name_plural = 'Hired Employees'
    
class InterestedEmployee(models.Model):
    job = models.ForeignKey(Employee,models.CASCADE)
    linked_employee = models.ForeignKey(employeeModels.Employee, models.CASCADE)
    interested_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return str(self.linked_employee)

class BrokenEquipmentReport(models.Model):
    CASE_TYPES = [
        ("U", 'Unread'),
        ("A", 'Acknowledged'),
        ("W", 'WIP'),
        ("B", 'Blocked'),
        ("C", 'Closed'),
    ]
    broken_system = models.ForeignKey(System, on_delete=models.CASCADE)
    date_filed = models.DateTimeField(auto_now_add=True)
    reported_broken_by = models.ForeignKey(employeeModels.Employee,models.PROTECT, null=True)
    notes = models.TextField()
    investigation = models.TextField(null=True,blank=True)
    status = models.CharField(choices=CASE_TYPES,max_length=1, null=True)

    def __str__(self):
        return self.status + " - " + str(self.broken_system)

class SystemInstance(models.Model):
    hours_rented = models.DecimalField(max_digits=6, decimal_places=2)
    system = models.ForeignKey(System,models.CASCADE)
    linked_gig = models.ForeignKey(Gig,models.CASCADE)

    def save(self, *args, **kwargs):
        if self.pk is None:
            for emp in Employee.objects.filter(linked_system=self.system):
                newemp = Employee(
                    linked_gig = self.linked_gig,
                    employee_type = emp.employee_type,
                    department = emp.department
                )
                newemp.save()
        super(SystemInstance, self).save(*args, **kwargs)

    def __str__(self):
        return self.system.department + " - " + self.system.name

    class Meta:
        verbose_name = 'Hired System'
        verbose_name_plural = 'Hired Systems'

# class Engineer(models.Model):
#     linked_engineer = models.ForeignKey(Employee,models.PROTECT)
#     linked_gig = models.ForeignKey(Gig,models.CASCADE)
#     department = models.CharField(max_length=1, choices=DEPARTMENTS)
#     hours_worked = models.DecimalField(max_digits=4, decimal_places=2)
#     shift_objects = GenericRelation('Shift')
    
# class Tech(models.Model):
#     linked_tech = models.ForeignKey(Employee,models.PROTECT)
#     linked_gig = models.ForeignKey(Gig,models.CASCADE)
#     department = models.CharField(max_length=1, choices=DEPARTMENTS)
#     hours_worked = models.DecimalField(max_digits=4, decimal_places=2)
#     shift_objects = GenericRelation('Shift')

# class Probie(models.Model):
#     linked_probie = models.ForeignKey(Employee,models.PROTECT)
#     linked_gig = models.ForeignKey(Gig,models.CASCADE)
#     department = models.CharField(max_length=1, choices=DEPARTMENTS)
#     hours_worked = models.DecimalField(max_digits=4, decimal_places=2)
#     shift_objects = GenericRelation('Shift')
    
# class Load(models.Model):
#     IN_OR_OUT = [
#         ("I", 'In'),
#         ("O", 'Out'),
#     ]
#     type = models.CharField(max_length=1, choices=IN_OR_OUT)
#     linked_tech = models.ForeignKey(Employee,models.PROTECT)
#     linked_gig = models.ForeignKey(Gig,models.CASCADE)
#     department = models.CharField(max_length=1, choices=DEPARTMENTS)
#     hours_worked = models.DecimalField(max_digits=4, decimal_places=2)
#     shift_objects = GenericRelation('Shift')

class Shift(models.Model):
    time_in = models.DateTimeField()
    time_out = models.DateTimeField()
    total_hours = models.DecimalField(max_digits=4, decimal_places=2)
    processed = models.BooleanField(default=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    def save(self):
        self.total_hours = (self.time_out-self.time_in).total_seconds()/3600
        super(Shift, self).save()

    def __str__(self):
        return self.content_object.__str__() + " - " + str(self.total_hours)

class Signup(models.Model):
    is_open = models.BooleanField(default=False)
    class Meta:
        verbose_name = 'Sign Up Status'
        verbose_name_plural = 'Sign Up Status'

    def __str__(self):
        return "Signup - Currently open" if self.is_open else "Signup - Currently Closed"
