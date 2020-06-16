from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin, Group
)

class Wage(models.Model):
    name = models.CharField(max_length=100,unique=True)
    amount = models.DecimalField(max_digits=4, decimal_places=2, default=11.80)

    def __str__(self):
        return f'{self.name} - ${self.amount}'

Group.add_to_class('hourly_rate', models.ForeignKey(Wage,models.PROTECT))


class EmployeeManager(BaseUserManager):
    def create_user(self, first_name, last_name, email, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(
            email=self.normalize_email(email),
            first_name = first_name,
            last_name = last_name,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_staffuser(self, first_name, last_name, email, password):
        user = self.create_user(
            first_name,
            last_name,
            email,
            password=password,
        )
        user.staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, email, password):
        user = self.create_user(
            first_name,
            last_name,
            email,
            password=password,
        )
        user.staff = True
        user.admin = True
        user.save(using=self._db)
        return user

class Employee(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255,unique=True,)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    bnum = models.IntegerField(null=True, verbose_name="B Number")
    phone_number = PhoneNumberField(null=True)
    active = models.BooleanField(default=False, verbose_name="Current Employee")
    staff = models.BooleanField(default=False, verbose_name="Manager")
    admin = models.BooleanField(default=False, verbose_name="System Admin")
    objects = EmployeeManager()


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name','last_name']

    def get_full_name(self):
        return self.email
    get_full_name.short_description = "Email"

    def get_short_name(self):
        return self.first_name
    get_short_name.short_description = "First Name"

    def __str__(self):
        return self.first_name + " " + self.last_name
    __str__.short_description = "Full Name"

    def has_perm(self, perm, obj=None):
        return PermissionsMixin.has_perm(self, perm, obj=None)

    def has_module_perms(self, app_label):
        return PermissionsMixin.has_module_perms(self, app_label)
    @property
    def is_staff(self):
        "Is the user a member of staff?"
        return self.staff

    @property
    def is_superuser(self):
        "Is the user a admin member?"
        return self.admin

    @property
    def is_active(self):
        "Is the user active?"
        return self.active

class Notification(models.Model):
    MESSAGE_TYPES = [
        ("normal", 'Normal'),
        ("uk-alert-success", 'Success'),
        ("uk-alert-warning", 'Warning'),
        ("uk-alert-danger", 'Danger/Error'),
    ]
    name = models.CharField(max_length=150)
    groups_to_send_to = models.ManyToManyField(
        Group,
        blank=True,
        help_text='Send the notification to the following groups.',
    )
    message = models.TextField()
    message_type = models.CharField(choices=MESSAGE_TYPES, max_length=16, default="normal")
    date_published = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.date_published) + " - " + self.name 

class NewEmployeesAllowed(models.Model):
    is_open = models.BooleanField(default=False)
    class Meta:
        verbose_name = 'Allow new Employees?'
        verbose_name_plural = 'Allow new Employees?'

    def __str__(self):
        return "Allowing new Employees" if self.is_open else "Employee Onboarding Closed"