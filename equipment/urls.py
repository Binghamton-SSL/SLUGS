from django.urls import path
from . import views

app_name = "equipment"
urlpatterns = [
    path("<system_id>/report/", views.reportBroken.as_view(), name="report"),
]
