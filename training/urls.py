from django.urls import path
from . import views

app_name = "training"
urlpatterns = [
    path("", views.index.as_view(), name="index"),
]
