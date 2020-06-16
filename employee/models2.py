from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class EmployeeManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, is_staff=False, is_admin=False):
        if not email:
            raise ValueError("Users must have a valid email")
        if not first_name:
            raise ValueError("Users must have a fName")
        if not last_name:
            raise ValueError("Users must have a lName")
        if not password:
            raise ValueError("Users must have a password")
        usr = self.model(
            email = self.normalize_email(email),
            usr.first_name = first_name,
            usr.last_name = last_name,
        )
        usr.staff = is_staff,
        usr.admin = is_admin,
        usr.set_password(password)
        usr.save(using=self._db)
        return usr
    
    def create_staffuser(self, email, first_name, last_name, password=None):
        user = self.create_user(
            email,
            first_name,
            last_name,
            password,
            is_staff=True,
        )
        return user
    
    def create_superuser(self, email, first_name, last_name, password=None):
        user = self.create_user(
            email,
            first_name,
            last_name,
            password,
            is_staff=True,
            is_admin=True,
        )
        return user
    

class Employee(AbstractBaseUser):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    bnum = models.IntegerField(null=True)
    phone_number = models.IntegerField(null=True)
    email = models.EmailField(unique=True)
    
    active = models.BooleanField(default=True)
    staff = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)
    # created = models.DateTimeField(editable=False)
    # modified = models.DateTimeField()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name','last_name']
    objects = EmployeeManager()

    def get_full_name(self):
        return self.first_name + " " + self.last_name

    def get_short_name(self):
        return self.first_name

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        return self.staff
    @property
    def is_admin(self):
        return self.admin
    @property
    def is_active(self):
        return self.active

    # def save(self, *args, **kwargs):
    #     if not self.id:
    #         self.created = timezone.now()
    #     self.modified = timezone.now()
    #     return super(Employee, self).save(*args, **kwargs)


# class Position(models.Model):
#     POSITION_CHOICES = [
#         ("NH", 'New Hire'),
#         ("L-0", 'Lighting - Probie'),
#         ("L-1", 'Lighting - Tech'),
#         ("L-2", 'Lighting - Small Engineer'),
#         ("L-3", 'Lighting - Medium Engineer'),
#         ("L-4", 'Lighting - Large Engineer'),
#         ("S-0", 'Sound - Probie'),
#         ("S-1", 'Sound - Tech'),
#         ("S-2", 'Sound - Junior Engineer'),
#         ("S-3", 'Sound - Senior Engineer'),
#         ("C-0", 'Custom - Low'),
#         ("C-1", 'Custom - Medium'),
#         ("C-2", 'Custom - High'),
#         ("MLST", 'Manager - Lighting - Shop Tech'),
#         ("MLD", 'Manager - Lighting - Director'),
#         ("MSST", 'Manager - Sound - Shop Tech'),
#         ("MSD", 'Manager - Sound - Director'),
#         ("MFD", 'Manager - Financial Director'),
#         ("MTD", 'Manager - Tech Director'),
#         ("MAM", 'Manager - Assistant Manager'),
#         ("MGM", 'Manager - General Manager'),
#     ]
#     position = models.CharField(max_length=5, choices=POSITION_CHOICES)
#     linked_employee = models.ForeignKey(Employee,on_delete=models.CASCADE)
#     created = models.DateTimeField(editable=False)
#     modified = models.DateTimeField()
    
#     def save(self, *args, **kwargs):
#         if not self.id:
#             self.created = timezone.now()
#         self.modified = timezone.now()
#         return super(Position, self).save(*args, **kwargs)
