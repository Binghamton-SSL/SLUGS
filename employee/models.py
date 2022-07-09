import os
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import Group
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.auth.models import AbstractUser
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone
from dateutil.relativedelta import *
import html
from dateutil.rrule import rrule, WEEKLY
import functools

from tinymce.models import HTMLField
from phonenumber_field.modelfields import PhoneNumberField
from jsignature.fields import JSignatureField

from employee.utils import auto_place_group_user


class EmployeeManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(email, password, **extra_fields)


class Employee(AbstractUser):
    """
    Employees that work or have worked for Binghamton Sound, Staging, and Lighting. Contains basic contact and employment info. 
    An employee's outstanding :model:`employee.paperwork` is also available.
    """
    username = None
    email = models.EmailField(_("email address"), unique=True)
    preferred_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="The first name you prefer to go by. This could be a chosen name or a nickname. This is not required.",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    bnum = models.CharField(null=True, max_length=12, verbose_name="B Number")
    phone_number = PhoneNumberField(null=True)
    is_grad_student = models.BooleanField(default=False, verbose_name="Currently a Graduate Student")
    graduation_year = models.IntegerField(blank=True, null=True, help_text="The year you receive(d) your undergraduate degree")
    final_year_with_bssl = models.IntegerField(blank=True, null=True, verbose_name="Final year @ BSSL", help_text="The final year you will be a fully matriculated student at Binghamton University, be it at the undergrad or graduate level. Defaults on save to your Graduation year unless a Grad Student.")
    end_of_employment = models.DateField(blank=True, null=True)
    signature = JSignatureField(
        null=True,
        blank=True,
        help_text="If on a mobile device, please turn it sideways to sign on a larger surface",
    )
    employee_notes = HTMLField(
        blank=True,
        null=True,
        help_text='Think of this as a "permanent record". Note anything important about this employee that should stick around. DO NOT delete anything from this unless you know what you\'re doing.',
    )
    paperwork = models.ManyToManyField(
        to="employee.Paperwork", through="employee.PaperworkForm"
    )
    is_active = models.BooleanField(default=False, verbose_name="Current Employee")
    is_staff = models.BooleanField(default=False, verbose_name="Manager")
    is_superuser = models.BooleanField(default=False, verbose_name="System Admin")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    date_joined = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date Hired",
        help_text="Defaults to datetime the employee signed up for SLUGS",
    )

    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"

    objects = EmployeeManager()

    def save(self, *args, **kwargs):
        if self.final_year_with_bssl is None and self.graduation_year is not None and self.is_grad_student is False:
            self.final_year_with_bssl = self.graduation_year
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{(self.preferred_name if self.preferred_name else self.first_name)} {self.last_name} ({self.email})"

    def paperwork_outstanding(self):
        papers = []
        for form in PaperworkForm.objects.filter(
            employee=self.pk, processed=False
        ).all():
            papers.append(form.form.form_name)
        return ", ".join(papers)

    def employee_metrics(self):
        jobs_held = set([job.position for job in self.job_set.all()])
        return format_html("""
            <div style="display: flex; flex-direction: column;">
                <div class="metric-container" style="display: flex; margin: 0px auto 1rem auto;">
                    <div class="number-metric">
                        <p class="metric-title">Total jobs worked</p>
                        <p class="metric-number">{6}</p>
                    </div>
                    <div class="number-metric">
                        <p class="metric-title">Total trainings attended</p>
                        <p class="metric-number">{7}</p>
                    </div>
                    <div class="number-metric">
                        <p class="metric-title">Time with company</p>
                        <p class="metric-number">{8}</p>
                    </div>
                    <div class="number-metric">
                        <p class="metric-title">Staffing score</p>
                        <p class="metric-number">{11}</p>
                    </div>
                </div>
                <div class="graph-flex metric-container" style="display: flex">
                    <div>
                        <div style="position: relative; margin: auto">
                            <p class="metric-title" >Job interest/placed over employee lifetime</p>
                            <canvas id="jobsOverLifetime"></canvas>
                        </div>
                    </div>
                    <div style="position: relative; margin: auto">
                        <p class="metric-title" >Types of Jobs Worked</p>
                        <canvas id="jobsTypesOverLifetime"></canvas>
                    </div>
                </div>
            </div>
            <style>
                .graph-flex > * {{
                    width: 50%;
                }}
                .number-metric {{
                    border: 1px solid white;
                    padding: 0.5rem;
                    margin: 0px 1rem 0px 1rem;
                    text-align: center;
                }}
                .metric-title {{
                    font-size: 1rem!important;
                    font-weight: bold!important;
                }}
                .metric-number {{
                    font-size: 2rem!important;
                }}
            @media (max-width: 767px) {{
                .readonly {{
                    width: 100%;
                }}
                .metric-container {{
                    flex-direction: column
                }}
                .graph-flex > * {{
                    width: 100%!important;
                }}
            }}
            </style>
            <script>
            const jobsOverLifetimedata = {{
                labels: {0},
                datasets: [
                    {{
                        label: "{1}",
                        backgroundColor: '#009961',
                        borderColor: '#009961',
                        data: {2},
                    }},
                    {{
                        "type": "bar",
                        label: "{9}",
                        backgroundColor: '#fff',
                        borderColor: '#fff',
                        data: {10},
                    }},
                ]
            }};

            const jobsOverLifetimeconfig = {{
                type: 'line',
                data: jobsOverLifetimedata,
                options: {{
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            ticks: {{
                                precision: 0,
                            }},
                        }}
                    }}
                }}
            }};

            const jobsOverLifetime = new Chart(
                document.getElementById('jobsOverLifetime'),
                jobsOverLifetimeconfig
            );

            const jobsTypesOverLifetimedata = {{
                labels: {3},
                datasets: [
                    {{
                        label: "{4}",
                        backgroundColor: ['#009961', "#000"],
                        borderColor: '#fff',
                        data: {5},
                    }},
                ]
            }};

            const jobsTypesOverLifetimeconfig = {{
                type: 'polarArea',
                data: jobsTypesOverLifetimedata,
                options: {{
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            ticks: {{
                                precision: 0,
                            }},
                        }}
                    }}
                }}
            }};

            const jobsTypesOverLifetime = new Chart(
                document.getElementById('jobsTypesOverLifetime'),
                jobsTypesOverLifetimeconfig
            );
            </script>

        """,
        mark_safe(str([dt.strftime('%m.%d.%y')+"-"+((dt+relativedelta(days=+6)).strftime('%m.%d.%y')) for dt in rrule(WEEKLY, byweekday=1,dtstart=self.job_set.order_by("gig__start").first().gig.start, until=self.job_set.order_by("gig__start").last().gig.start)])),
        mark_safe(f"{self.preferred_name if self.preferred_name else self.first_name}'s jobs worked per week"),
        mark_safe(str([self.job_set.filter(gig__start__gte=dt, gig__end__lt=(dt+relativedelta(weeks=+1))).count() for dt in rrule(WEEKLY, byweekday=1,dtstart=self.job_set.order_by("gig__start").first().gig.start, until=self.job_set.order_by("gig__start").last().gig.start)])),
        mark_safe(str([position.name for position in jobs_held])),
        mark_safe(f"{self.preferred_name if self.preferred_name else self.first_name}'s types of jobs worked"),
        mark_safe(str([self.job_set.filter(position=pos).count() for pos in jobs_held])),
        str(self.job_set.count()),
        str(self.trainee_set.count()),
        naturaltime(self.end_of_employment - self.date_joined.date() if self.end_of_employment else timezone.now()-self.date_joined),
        mark_safe(f"{self.preferred_name if self.preferred_name else self.first_name}'s jobs requested per week"),
        mark_safe(str([self.jobinterest_set.filter(job__gig__start__gte=dt, job__gig__end__lt=(dt+relativedelta(weeks=+1))).count() for dt in rrule(WEEKLY, byweekday=1,dtstart=self.job_set.order_by("gig__start").first().gig.start, until=self.job_set.order_by("gig__start").last().gig.start)])),
        str(functools.reduce(lambda a, b: a+(1 if self.job_set.filter(gig__pk=b[0]).first() is not None else -1), self.jobinterest_set.all().values_list("job__gig").distinct(), 0)*((timezone.now() - self.job_set.order_by("-gig__start").first().gig.start).days if self.job_set.order_by("-gig__start").first() is not None else 0))
        )


class OfficeHours(models.Model):
    """
    Managerial Office Hours recorded outside of shows.
    """
    position = models.ForeignKey(
        Group, default="Manager", to_field="name", on_delete=models.PROTECT
    )
    employee = models.ForeignKey("employee.Employee", on_delete=models.CASCADE)
    shifts = GenericRelation("finance.Shift")

    class Meta:
        verbose_name_plural = "Office Hours"

    def __str__(self):
        return "Office Hours"


class PaperworkForm(models.Model):
    """
    All :model:`employee.paperwork` documents from every employee in order of upload date *(not including timesheets)*. 
    You also have the ability to add paperwork forms to individuals via this model. 
    """
    def user_dir_path(instance, filename):
        fileName, fileExtension = os.path.splitext(filename)
        return f"uploads/{instance.employee.bnum}/{instance.employee.bnum}_{instance.employee.first_name[0].upper()}{instance.employee.last_name}_{str(instance.form)}{fileExtension}"  # noqa

    form = models.ForeignKey("employee.Paperwork", on_delete=models.PROTECT)
    employee = models.ForeignKey("employee.Employee", on_delete=models.CASCADE)
    pdf = models.FileField(upload_to=user_dir_path, blank=True, null=True)
    uploaded = models.DateTimeField(blank=True, null=True)
    requested = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.employee} - {self.form}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        auto_place_group_user(self.employee)


class Paperwork(models.Model):
    """
    Basic paperwork model used in conjunction with :model:`employee.PaperworkForm` to send out paperwork to employees. 
    Basic info about paperwork to be distributed.
    """
    form_name = models.CharField(max_length=256)
    form_pdf = models.FileField(upload_to="forms/")
    uploaded = models.DateTimeField(auto_now_add=True)
    handed_in = models.CharField(max_length=512, null=True, blank=True)
    required_for_employment = models.BooleanField(default=False)
    required_for_payroll = models.BooleanField(default=False)
    can_auto_sign = models.BooleanField(default=False)
    auto_sign_layout = models.TextField(blank=True, default="[]")
    edited = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        for employee in self.employee_set.all():
            auto_place_group_user(employee)

    def __str__(self):
        return f"{self.form_name} (Last Edited: {self.edited.strftime('%m.%d.%y')})"

    def associated_forms(self):
        ret = ""
        for form in (
            PaperworkForm.objects.filter(form=self.pk, employee__is_active=True)
            .order_by("processed")
            .all()
        ):
            line = "<div style='margin: .25rem 0 .25rem 0'>"
            line += (
                f"<a href='/media/{form.pdf}'>{form}</a>"
                if form.pdf
                else f"<span>{form}</span>"
            )
            line += "<b> - NOT PROCESSED</b>" if not form.processed else ""
            line += "</div><br>"
            ret += line
        return format_html(ret)

    class Meta:
        verbose_name = "Paperwork"
        verbose_name_plural = "Paperwork"
