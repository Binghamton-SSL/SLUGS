from django.urls import path
from . import models

app_name = "utils"
urlpatterns = [
    path("latest/events.ics", models.ShowFeed(), name="showFeed"),
    path("latest/lighting_work.ics", models.LightingFeed(), name="lightingFeed"),
    path("latest/sound_work.ics", models.SoundFeed(), name="soundFeed"),
    path("latest/stage_work.ics", models.StageFeed(), name="stageFeed"),
]
