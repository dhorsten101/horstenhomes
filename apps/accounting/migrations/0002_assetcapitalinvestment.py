from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

	dependencies = [
		("properties", "0010_unit_purchase_date"),
		("accounting", "0001_initial"),
	]

	operations = [
		migrations.CreateModel(
			name="AssetCapitalInvestment",
			fields=[
				("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
				("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
				("updated_at", models.DateTimeField(auto_now=True)),
				("investment_date", models.DateField(db_index=True, default=django.utils.timezone.now)),
				("amount", models.DecimalField(decimal_places=2, max_digits=14)),
				("description", models.CharField(blank=True, max_length=500)),
				(
					"related_property",
					models.ForeignKey(
						blank=True,
						null=True,
						on_delete=django.db.models.deletion.CASCADE,
						related_name="capital_investments",
						to="properties.property",
					),
				),
				(
					"unit",
					models.ForeignKey(
						blank=True,
						null=True,
						on_delete=django.db.models.deletion.CASCADE,
						related_name="capital_investments",
						to="properties.unit",
					),
				),
			],
			options={
				"ordering": ("-investment_date", "-created_at"),
			},
		),
		migrations.AddIndex(
			model_name="assetcapitalinvestment",
			index=models.Index(fields=["related_property", "investment_date"], name="accounting__related_4a8f2d_idx"),
		),
		migrations.AddIndex(
			model_name="assetcapitalinvestment",
			index=models.Index(fields=["unit", "investment_date"], name="accounting__unit_id_7c2b91_idx"),
		),
		migrations.AddConstraint(
			model_name="assetcapitalinvestment",
			constraint=models.CheckConstraint(
				condition=models.Q(
					models.Q(("related_property__isnull", False), ("unit__isnull", True)),
					models.Q(("related_property__isnull", True), ("unit__isnull", False)),
					_connector="OR",
				),
				name="accounting_capital_investment_property_xor_unit",
			),
		),
	]
