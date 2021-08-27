from django_unicorn.components import UnicornView
from utils.models import signupStatus
from gig.models import Gig
from django.utils import timezone


class SignupstatusView(UnicornView):
    signup = signupStatus.objects.first()
    plz_close = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plz_close = (
            self.signup.is_open
            and len(
                Gig.objects.filter(
                    start__gte=timezone.now(), job__employee=None, published=True
                )
            )
            == 0
        )

    def toggle(self):
        self.signup.is_open = False if self.signup.is_open else True
        self.signup.save()
        self.plz_close = (
            self.signup.is_open
            and len(
                Gig.objects.filter(
                    start__gte=timezone.now(), job__employee=None, published=True
                )
            )
            == 0
        )
