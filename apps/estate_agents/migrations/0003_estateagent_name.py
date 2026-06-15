from django.db import migrations, models


def set_agent_names_from_contact(apps, schema_editor):
	EstateAgent = apps.get_model("estate_agents", "EstateAgent")
	for agent in EstateAgent.objects.select_related("contact").all():
		if agent.contact_id:
			agent.name = agent.contact.display_name
			agent.save(update_fields=["name"])


class Migration(migrations.Migration):

	dependencies = [
		("estate_agents", "0002_contact_link"),
	]

	operations = [
		migrations.RemoveIndex(
			model_name="estateagent",
			name="estate_agen_is_acti_contact_idx",
		),
		migrations.AddField(
			model_name="estateagent",
			name="name",
			field=models.CharField(blank=True, default="", max_length=200),
		),
		migrations.RunPython(set_agent_names_from_contact, migrations.RunPython.noop),
		migrations.AlterField(
			model_name="estateagent",
			name="name",
			field=models.CharField(db_index=True, max_length=200),
		),
		migrations.AlterModelOptions(
			name="estateagent",
			options={"ordering": ("name",)},
		),
		migrations.AddIndex(
			model_name="estateagent",
			index=models.Index(fields=["is_active", "name"], name="estate_agen_is_acti_name_idx"),
		),
	]
