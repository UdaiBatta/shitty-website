from django.db import migrations


RETIRED_TITLES = (
    "COO OF FUCKERY",
    "FUCKERY POTTER LIKE HARRY POTTER",
)


def deactivate_retired_roles(apps, schema_editor):
    Job = apps.get_model("jobs", "Job")
    Job.objects.filter(title__in=RETIRED_TITLES).update(is_active=False)


def reactivate_retired_roles(apps, schema_editor):
    Job = apps.get_model("jobs", "Job")
    Job.objects.filter(title__in=RETIRED_TITLES).update(is_active=True)


class Migration(migrations.Migration):
    dependencies = [("jobs", "0001_initial")]

    operations = [
        migrations.RunPython(deactivate_retired_roles, reactivate_retired_roles),
    ]
