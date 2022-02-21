from django.core.management.base import BaseCommand

from employee.models import Employee


class Command(BaseCommand):
    help = "Checks against all active employees to see who is missing paperwork"

    def add_arguments(self, parser):
        parser.add_argument(
            "--forms",
            action="store_true",
            help="Show forms that are missing for each individual",
        )

    def handle(self, *args, **options):
        for emp in Employee.objects.filter(is_active=True):
            is_good = True
            paperwork_missing = []
            unprocessed = emp.paperworkform_set.filter(processed=False)
            if unprocessed.count() > 0:
                is_good = False
                paperwork_missing = unprocessed.all()
            if not is_good:
                print(
                    f"{(emp.preferred_name if emp.preferred_name else emp.first_name)} {emp.last_name}"
                    if not options["forms"]
                    else f"{(emp.preferred_name if emp.preferred_name else emp.first_name)} {emp.last_name} - {[form.form.form_name for form in paperwork_missing.all()]}"
                )
