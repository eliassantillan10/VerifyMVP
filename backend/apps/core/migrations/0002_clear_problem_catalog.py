from django.db import migrations


def clear_problem_catalog(apps, _schema_editor):
    apps.get_model("core", "Problem").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0001_problem_catalog")]

    operations = [
        migrations.RunPython(clear_problem_catalog, migrations.RunPython.noop),
    ]
