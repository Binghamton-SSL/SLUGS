from django_unicorn.components import UnicornView
from utils.models import onboardingStatus


class OnboardingstatusView(UnicornView):
    onboarding = onboardingStatus.objects.first()

    def toggle(self):
        self.onboarding.is_open = False if self.onboarding.is_open else True
        self.onboarding.save()
