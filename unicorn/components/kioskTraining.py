from django_unicorn.components import UnicornView

from finance.models import Shift
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from training.models import Trainee, Training


class KiosktrainingView(UnicornView):
    ongoing_trainings = None
    training_error_message = None
    training_shown = []
    trainee_content_type = ContentType.objects.get(model="trainee").id
    last_training_update = timezone.now()

    def toggle_modal(self, gig_id):
        if gig_id in self.training_shown:
            self.training_shown.remove(gig_id)
        else:
            self.training_shown.append(gig_id)
        self.update_training_status()

    def toggle_clock(self, trainee_id):
        trainee = Trainee.objects.get(pk=trainee_id)
        shifts = Shift.objects.filter(
                    object_id=trainee.id,
                    content_type_id=self.trainee_content_type,
                    time_out=None
                )
        clocked_in = shifts.order_by('time_in').last() if shifts.count() > 0 else None
        if(clocked_in):
            clocked_in.time_out = timezone.now()
            clocked_in.save()
            trainee.save()
        else:
            trainee.shifts.create(time_in=timezone.now())
            trainee.save()
        self.update_training_status()

    def update_training_status(self):
        self.ongoing_trainings = [{"training": training, "trainees": [], "unpaid_trainees": None, "shown": True if training.pk in self.training_shown else False} for training in Training.objects.filter(date__lte=(timezone.now() + timezone.timedelta(hours=+29)), date__gte=(timezone.now() + timezone.timedelta(hours=-29))).order_by('date')]
        for training in self.ongoing_trainings:
            trainee_set = (
                Trainee.objects.filter(training=training["training"].pk) if training['training'].paid
                else Trainee.objects.filter(training=training["training"].pk, override_allow_paid=True)
            )
            training['unpaid_trainees'] = (
                Trainee.objects.filter(training=training["training"].pk, override_allow_paid=False) if not training['training'].paid
                else None
            )
            for trainee in trainee_set:
                # Are they currently clocked in?
                employee_shifts = Shift.objects.filter(
                    object_id=trainee.id,
                    content_type_id=self.trainee_content_type,
                    time_out=None
                )
                clocked_in = employee_shifts.order_by('time_in').last() if employee_shifts.count() > 0 else None

                training['trainees'].append([trainee, clocked_in])
        self.last_training_update = timezone.now()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_training_status()