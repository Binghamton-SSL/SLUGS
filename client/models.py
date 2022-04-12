from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class Organization(models.Model):
    name = models.CharField(max_length=200)
    SA_account_num = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.name}{' - NON-SA' if self.SA_account_num is None else ''}"


class OrgContact(models.Model):
    name = models.CharField(max_length=200)
    organization = models.ForeignKey(Organization, models.PROTECT)
    phone_number = PhoneNumberField(null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = "Organization Contact"

    def __str__(self):
        return f"{self.name} - {self.organization.name}"
