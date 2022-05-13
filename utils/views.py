from django.http.response import HttpResponse
from django.views.generic.base import View
import os
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from SLUGS.views import isAdminMixin


class restartServer(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect("%s?next=%s" % (reverse("login"), request.path))
        os.system("touch ~/slugs.bssl.binghamtonsa.org/tmp/restart.txt")
        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Server will restart momentarily. Expect a 1-2 minute interruption to service.",
        )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return HttpResponse(
            "Server will restart momentarily. Expect a 1-2 minute interruption to service."
        )
