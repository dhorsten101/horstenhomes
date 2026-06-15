# Generated manually

import django.db.models.deletion
from django.db import migrations, models


def link_managing_agents_to_contacts(apps, schema_editor):
	Contact = apps.get_model("contacts", "Contact")
	ManagingAgent = apps.get_model("managing_agents", "ManagingAgent")
	for agent in ManagingAgent.objects.all():
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
		("managing_agents", "0001_initial"),
	]

	operations = [
		migrations.AddField(
			model_name="managingagent",
			name="contact",
			field=models.ForeignKey(
				null=True,
				on_delete=django.db.models.deletion.PROTECT,
				related_name="managing_agents",
				to="contacts.contact",
			),
		),
		migrations.RunPython(link_managing_agents_to_contacts, migrations.RunPython.noop),
		migrations.AlterField(
			model_name="managingagent",
			name="contact",
			field=models.ForeignKey(
				on_delete=django.db.models.deletion.PROTECT,
				related_name="managing_agents",
				to="contacts.contact",
			),
		),
		migrations.RemoveIndex(
			model_name="managingagent",
			name="managing_ag_is_acti_9a497d_idx",
		),
		migrations.RemoveField(model_name="managingagent", name="address"),
		migrations.RemoveField(model_name="managingagent", name="email"),
		migrations.RemoveField(model_name="managingagent", name="name"),
		migrations.RemoveField(model_name="managingagent", name="phone"),
		migrations.AddIndex(
			model_name="managingagent",
			index=models.Index(fields=["is_active", "contact"], name="managing_a_is_acti_contact_idx"),
		),
		migrations.AlterModelOptions(
			name="managingagent",
			options={"ordering": ("contact__display_name",)},
		),
	]
