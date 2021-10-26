from django.core.management.base import BaseCommand

from employee.models import Employee


class Command(BaseCommand):
    help = "Checks against all active employees to see who is missing paperwork"

    def add_arguments(self, parser):
        parser.add_argument(
            '--forms',
            action='store_true',
            help='Show forms that are missing for each individual',
        )

    def handle(self, *args, **options):
        for emp in Employee.objects.filter(is_active=True):
            is_good = True
            paperwork_missing = []
            for paperwork in emp.paperworkform_set.all():
                if  not paperwork.processed:
                    is_good = False
                    paperwork_missing.append(paperwork.form.form_name)
            if not is_good:
                print(f'{emp.first_name} {emp.last_name}' if not options['forms'] else f'{emp.first_name} {emp.last_name} - {", ".join(paperwork_missing)}')