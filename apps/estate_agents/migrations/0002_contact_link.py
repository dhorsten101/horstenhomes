# Generated manually

import django.db.models.deletion
from django.db import migrations, models


def link_estate_agents_to_contacts(apps, schema_editor):
	Contact = apps.get_model("contacts", "Contact")
	EstateAgent = apps.get_model("estate_agents", "EstateAgent")
	for agent in EstateAgent.objects.all():
		if agent.contact_id:
			continue
		contact = Contact.objects.create(
			display_name=agent.name,
			email=agent.email or "",
			phone=agent.phone or "",
			address_id=agent.address_id,
		)
		agent.contact = contact
		agent.save(update_fields=["contact"])


class Migration(migrations.Migration):

	dependencies = [
		("contacts", "0001_initial"),
		("estate_agents", "0001_initial"),
	]

	operations = [
		migrations.AddField(
			model_name="estateagent",
			name="contact",
			field=models.ForeignKey(
				null=True,
				on_delete=django.db.models.deletion.PROTECT,
				related_name="estate_agents",
				to="contacts.contact",
			),
		),
		migrations.RunPython(link_estate_agents_to_contacts, migrations.RunPython.noop),
		migrations.AlterField(
			model_name="estateagent",
			name="contact",
			field=models.ForeignKey(
				on_delete=django.db.models.deletion.PROTECT,
				related_name="estate_agents",
				to="contacts.contact",
			),
		),
		migrations.RemoveIndex(
			model_name="estateagent",
			name="estate_agen_is_acti_45ecb2_idx",
		),
		migrations.RemoveField(model_name="estateagent", name="address"),
		migrations.RemoveField(model_name="estateagent", name="email"),
		migrations.RemoveField(model_name="estateagent", name="name"),
		migrations.RemoveField(model_name="estateagent", name="phone"),
		migrations.AddIndex(
			model_name="estateagent",
			index=models.Index(fields=["is_active", "contact"], name="estate_agen_is_acti_contact_idx"),
		),
		migrations.AlterModelOptions(
			name="estateagent",
			options={"ordering": ("contact__display_name",)},
		),
	]
