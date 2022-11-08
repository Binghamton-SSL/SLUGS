from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class Organization(models.Model):
    """
    All main contacts for all organizations that have previously ever been in a BSSL interaction. 
    This includes their name and :model:`client.OrgContact` .
    """
    name = models.CharField(max_length=200)
    SA_account_num = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.name}{' - NON-SA' if self.SA_account_num is None else ''}"


class Contact(models.Model):
    name = models.CharField(max_length=200)
    phone_number = PhoneNumberField(null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name


class OrgContact(models.Model):
    """
    Organizations that have interacted with BSSL. 
    This includes the name of the organization and there SA number *if applicable*.
    If the organization is not chartered by SA it will be labeled **"NON-SA"**.
    """
    organization = models.ForeignKey(Organization, models.PROTECT)
    name = models.CharField(max_length=200)
    phone_number = PhoneNumberField(null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = "Organization Contact"

    def __str__(self):
        return f"{self.name} - {self.organization.name}"


class Communication(models.Model):
    """
    A communication between a BSSL employee and a contact. Communications are linked to: gigs, estimates, organizations, org_contacts, employees, locations, and trainings
    """
    COMMUNICATION_MODELS = [
        ("I", "In Person"),
        ("E", "Email"),
        ("P", "Phone"),
        ("T", "Text"),
        ("F", "Form"),
        ("O", "Other"),
    ]
    employees = models.ManyToManyField("employee.Employee", blank=True)
    contacts = models.ManyToManyField("client.OrgContact", blank=True)
    organizations = models.ManyToManyField("client.Organization", blank=True)
    gigs = models.ManyToManyField("gig.Gig", blank=True)
    estimates = models.ManyToManyField("finance.Estimate", blank=True)
    locations = models.ManyToManyField("location.Location", blank=True)
    trainings = models.ManyToManyField("training.Training", blank=True)
    via = models.CharField(choices=COMMUNICATION_MODELS, max_length=1)
    note = models.TextField(blank=True)