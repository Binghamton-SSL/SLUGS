from datetime import datetime
import decimal
from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.forms import ValidationError
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse
from tinymce.models import HTMLField
from django.contrib.auth.models import Group
from django.db.models import Q, Sum

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

DELIVERY_METHODS = [
    ("H", "Vendor Delivery"),
    ("S", "Vendor Shipping"),
    ("P", "BSSL Delivery"),
    ("B", "BSSL Shipping"),
    ("O", "Other Arrangements"),

]


class SubcontractedEquipmentInstance(models.Model):
    equipment = models.ForeignKey("equipment.VendorEquipment", on_delete=models.PROTECT)
    subcontracted_equipment = models.ForeignKey("SubcontractedEquipment", on_delete=models.CASCADE)
    qty = models.IntegerField(default=1)
    description = models.CharField(max_length=200, blank=True, null=True)


class SubcontractedEquipment(models.Model):
    equipment = models.ManyToManyField("equipment.VendorEquipment", through="SubcontractedEquipmentInstance")
    vendor = models.ForeignKey("equipment.Vendor", on_delete=models.PROTECT)
    arrival = models.DateTimeField()
    returned = models.DateTimeField()
    delivery_method = models.CharField(max_length=1, choices=DELIVERY_METHODS)
    return_method = models.CharField(max_length=1, choices=DELIVERY_METHODS)
    purchase_order = models.CharField(max_length=64, null=True, blank=True)
    vendor_visible_to_client = models.BooleanField(default=False)
    client_provided = models.BooleanField(default=False)
    notes = HTMLField(blank=True, null=True)
    gig = models.ForeignKey("Gig", on_delete=models.CASCADE)
    signed_agreement = models.FileField(upload_to="vendors", null=True, blank=True)

    def get_printout_link(self):
        return format_html(
                "<a href='%s?time=%s'>%s</a><br>"
                % (
                    reverse("finance:vendor", args=(self.id,)),
                    datetime.now(),
                    f"Print Subcontracted Equipment Form - {self.vendor}",
                )
            )

    def __str__(self):
        return f"{self.vendor} - {self.gig}"

    class Meta:
        verbose_name_plural = "Subcontracted Equipment"


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
    subcontracted_equipment = models.ManyToManyField("SubcontractedEquipment", related_name="vendor_equipment")
    attachments = GenericRelation("utils.Attachment")

    def calculate_outflow(self):
        outflow = decimal.Decimal(0.00)
        for job in self.job_set.all():
            job_outflow = job.shifts.all().aggregate(Sum("cost"))['cost__sum']
            outflow += job_outflow if job_outflow is not None else decimal.Decimal(0.00)
        return round(outflow, 2)

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
            + str(self.org.name)
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


class BingoBoard(models.Model):
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE)
    available_for_play = models.BooleanField(default=True)
    tiles = models.ManyToManyField("BingoTile", through="TileOnBoard")
    bingo_achieved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.gig} Bingo Board ({'open' if self.available_for_play else 'closed'})"

    def choose_random_tile(self, currently_on_board=[]):
        depts_in_gig = set([d.department for d in self.gig.systems.all()]+["A"])
        available = BingoTile.objects.filter(Q(department__in=depts_in_gig) & Q(in_pool=True) & ~Q(pk__in=currently_on_board))
        chosen = available.order_by("?").first()
        tmp = currently_on_board.append(chosen.pk) if currently_on_board is not None else [chosen.pk]
        return (chosen, currently_on_board) if chosen is not None else None


    def save(self, *args, **kwargs):
        if self.pk is None:
            super().save(*args, **kwargs)
        currently_on_board = [t.pk for t in self.tiles.all()]
        # If not enough tiles on board, attempts to find unique tiles, if cannot find enough unique it resorts to choosing duplicates
        while self.tiles.count() < 16:
            try:
                tile = self.choose_random_tile(currently_on_board)
                if tile is not None:
                    TileOnBoard(tile=tile[0], board=self).save()
                    currently_on_board = tile[1]
                else:
                    raise Exception("No unique tiles left")
            except Exception:
                try:
                    tile = self.choose_random_tile([])
                    if tile is not None:
                        TileOnBoard(tile=tile[0], board=self).save()
                    else:
                        raise Exception("No unique tiles left")
                except Exception:
                    raise ValidationError("Not enough tiles in play to create a board for this show")
        return super().save(*args, **kwargs)


class BingoTile(models.Model):
    BINGO_DEPARTMENTS = [
        ("A", "All"),
        ("L", "Lighting"),
        ("S", "Sound"),
        ("M", "Manager"),
        ("O", "Other"),
        ("T", "Staging"),
    ]
    in_pool = models.BooleanField(default=True)
    department = models.CharField(choices=BINGO_DEPARTMENTS, max_length=1)
    action = models.CharField(max_length=61, null=False, blank=False)

    def __str__(self):
        return f"{self.get_department_display()} - {self.action}{' - RETIRED' if self.in_pool is False else ''}"


class TileOnBoard(models.Model):
    board = models.ForeignKey(BingoBoard, on_delete=models.CASCADE)
    tile = models.ForeignKey(BingoTile, on_delete=models.PROTECT)
    checked_by = models.ForeignKey(employee.Employee, null=True, blank=True, on_delete=models.CASCADE)
