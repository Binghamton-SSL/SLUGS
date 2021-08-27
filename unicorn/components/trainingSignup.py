from django_unicorn.components import UnicornView
from training.models import Training


class TrainingsignupView(UnicornView):
    is_signed_up_for_training = False
    full = None
    training_id = None
    user_id = None

    def checkIfSignedup(self):
        training = Training.objects.get(pk=self.training_id)
        self.is_signed_up_for_training = training.attendees.filter(
            pk=self.user_id
        ).exists()
        self.full = (
            (training.capacity <= training.attendees.count())
            and not self.is_signed_up_for_training
            if training.capacity
            else False
        )
        pass

    def __init__(self, *args, **kwargs):
        self.training_id = kwargs["training_id"]
        self.user_id = kwargs["emp_id"]
        self.checkIfSignedup()
        return super().__init__(*args, **kwargs)

    def toggleSignup(self):
        training = Training.objects.get(pk=self.training_id)
        if self.is_signed_up_for_training:
            training.attendees.remove(self.user_id)
        else:
            if training.capacity and (training.capacity <= training.attendees.count()):
                pass
            else:
                training.attendees.add(self.user_id)
        self.checkIfSignedup()
