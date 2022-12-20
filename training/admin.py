from django.contrib import admin
import nested_admin
from training.models import Training, Trainee, TrainingRequest
from django.contrib.auth.models import Group
from finance.admin import ShiftInlineAdmin


@admin.register(TrainingRequest)
class TrainingRequestAdmin(admin.ModelAdmin):
    filter_horizontal = ["systems"]
    list_filter = ["answered"]


class TraineeInlineAdmin(nested_admin.NestedStackedInline):
    autocomplete_fields = ["employee"]
    inlines = [ShiftInlineAdmin]
    model = Trainee
    extra = 0
    verbose_name = "Training Participant"
    verbose_name_plural = "Training Participants"


@admin.register(Training)
class TrainingAdmin(nested_admin.NestedModelAdmin):
    inlines = [TraineeInlineAdmin]
    list_display = ["__str__", "date"]
    filter_horizontal = ["trainers", "attendees", "systems"]
    autocomplete_fields = ["location"]

    def save_model(self, request, obj, form, change):
        if 'trainers' in form.changed_data:
            for trainer in form.cleaned_data['trainers']:
                Trainee.objects.get_or_create(
                    employee=trainer,
                    training=obj,
                    position=Group.objects.get(name="Manager"),
                    override_allow_paid=True
                )
        super().save_model(request, obj, form, change)


@admin.register(Trainee)
class TraineeAdmin(nested_admin.NestedModelAdmin):
    autocomplete_fields = ["position"]
    pass
