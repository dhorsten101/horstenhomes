from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		("properties", "0009_unit_agent_assignments"),
	]

	operations = [
		migrations.AddField(
			model_name="unit",
			name="purchase_date",
			field=models.DateField(blank=True, db_index=True, null=True),
		),
	]
