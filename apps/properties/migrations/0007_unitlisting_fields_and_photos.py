import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import apps.properties.models


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0006_unitlisting"),
    ]

    operations = [
        migrations.AddField(
            model_name="unitlisting",
            name="furnished",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="unitlisting",
            name="lease_term_months",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="unitlisting",
            name="parking_spaces",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="unitlisting",
            name="pet_policy",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="unitlisting",
            name="utilities_included",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.CreateModel(
            name="ListingPhoto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)),
                ("tags", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("image", models.FileField(upload_to=apps.properties.models._listing_photo_upload_to)),
                ("caption", models.CharField(blank=True, max_length=200)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("is_primary", models.BooleanField(db_index=True, default=False)),
                (
                    "listing",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="photos", to="properties.unitlisting"),
                ),
            ],
            options={
                "ordering": ["-is_primary", "sort_order", "created_at"],
                "abstract": False,
            },
        ),
        migrations.AddIndex(
            model_name="listingphoto",
            index=models.Index(fields=["listing", "is_primary"], name="properties__listin_9865c1_idx"),
        ),
    ]
