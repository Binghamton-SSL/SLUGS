from django.contrib import admin
import nested_admin
from training.models import Training, Trainee, TrainingRequest
from finance.admin import ShiftInlineAdmin


@admin.register(TrainingRequest)
class TrainingRequestAdmin(admin.ModelAdmin):
    filter_horizontal = ["systems"]


class TraineeInlineAdmin(nested_admin.NestedStackedInline):
    autocomplete_fields = ["employee"]
    inlines = [ShiftInlineAdmin]
    model = Trainee
    extra = 0


@admin.register(Training)
class TrainingAdmin(nested_admin.NestedModelAdmin):
    inlines = [TraineeInlineAdmin]
    filter_horizontal = ["trainers", "attendees", "systems"]


@admin.register(Trainee)
class TraineeAdmin(nested_admin.NestedModelAdmin):
    autocomplete_fields = ["position"]
    pass
