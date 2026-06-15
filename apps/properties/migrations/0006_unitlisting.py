import uuid

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0005_unit_properties__propert_8f85f0_idx_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="UnitListing",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)),
                ("tags", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=200)),
                ("summary", models.TextField(blank=True)),
                ("rent_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("deposit_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("available_from", models.DateField(blank=True, null=True)),
                ("is_published", models.BooleanField(db_index=True, default=False)),
                ("contact_email", models.EmailField(blank=True, max_length=254)),
                ("contact_phone", models.CharField(blank=True, max_length=40)),
                ("amenities", models.CharField(blank=True, help_text="Comma-separated list", max_length=250)),
                (
                    "unit",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="listing", to="properties.unit"),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddIndex(
            model_name="unitlisting",
            index=models.Index(fields=["is_published", "created_at"], name="properties__is_publ_6f2d7a_idx"),
        ),
    ]
