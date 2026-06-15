from django.db import migrations, models


def set_plan_currency_zar(apps, schema_editor):
    Plan = apps.get_model("entitlements", "Plan")
    Plan.objects.filter(currency="USD").update(currency="ZAR")


def set_plan_currency_usd(apps, schema_editor):
    Plan = apps.get_model("entitlements", "Plan")
    Plan.objects.filter(currency="ZAR").update(currency="USD")


class Migration(migrations.Migration):

    dependencies = [
        ("entitlements", "0002_alter_plan_currency"),
    ]

    operations = [
        migrations.AlterField(
            model_name="plan",
            name="currency",
            field=models.CharField(default="ZAR", max_length=3),
        ),
        migrations.RunPython(set_plan_currency_zar, set_plan_currency_usd),
    ]
