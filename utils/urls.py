from django.urls import path
from . import models
from . import views

app_name = "utils"
urlpatterns = [
    path("latest/events.ics", models.ShowFeed(), name="showFeed"),
    path(
        "latest/tentative_events.ics",
        models.TentativeShowFeed(),
        name="tentativeShowFeed",
    ),
    path("latest/lighting_work.ics", models.LightingFeed(), name="lightingFeed"),
    path("latest/sound_work.ics", models.SoundFeed(), name="soundFeed"),
    path("latest/stage_work.ics", models.StageFeed(), name="stageFeed"),
    path("<emp_id>/shifts.ics", models.EmployeeFeed(), name="employeeFeed"),
    path("server/restart", views.restartServer.as_view(), name="restartServer"),
]
