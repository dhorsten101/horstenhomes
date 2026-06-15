from django.db import migrations, models


def set_agent_names_from_contact(apps, schema_editor):
	RentalAgent = apps.get_model("rental_agents", "RentalAgent")
	for agent in RentalAgent.objects.select_related("contact").all():
		if agent.contact_id:
			agent.name = agent.contact.display_name
			agent.save(update_fields=["name"])


class Migration(migrations.Migration):

	dependencies = [
		("rental_agents", "0002_contact_link"),
	]

	operations = [
		migrations.RemoveIndex(
			model_name="rentalagent",
			name="rental_agen_is_acti_contact_idx",
		),
		migrations.AddField(
			model_name="rentalagent",
			name="name",
			field=models.CharField(blank=True, default="", max_length=200),
		),
		migrations.RunPython(set_agent_names_from_contact, migrations.RunPython.noop),
		migrations.AlterField(
			model_name="rentalagent",
			name="name",
			field=models.CharField(db_index=True, max_length=200),
		),
		migrations.AlterModelOptions(
			name="rentalagent",
			options={"ordering": ("name",)},
		),
		migrations.AddIndex(
			model_name="rentalagent",
			index=models.Index(fields=["is_active", "name"], name="rental_agen_is_acti_name_idx"),
		),
	]
