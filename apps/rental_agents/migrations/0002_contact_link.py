# Generated manually

import django.db.models.deletion
from django.db import migrations, models


def link_rental_agents_to_contacts(apps, schema_editor):
	Contact = apps.get_model("contacts", "Contact")
	RentalAgent = apps.get_model("rental_agents", "RentalAgent")
	for agent in RentalAgent.objects.all():
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
		("rental_agents", "0001_initial"),
	]

	operations = [
		migrations.AddField(
			model_name="rentalagent",
			name="contact",
			field=models.ForeignKey(
				null=True,
				on_delete=django.db.models.deletion.PROTECT,
				related_name="rental_agents",
				to="contacts.contact",
			),
		),
		migrations.RunPython(link_rental_agents_to_contacts, migrations.RunPython.noop),
		migrations.AlterField(
			model_name="rentalagent",
			name="contact",
			field=models.ForeignKey(
				on_delete=django.db.models.deletion.PROTECT,
				related_name="rental_agents",
				to="contacts.contact",
			),
		),
		migrations.RemoveIndex(
			model_name="rentalagent",
			name="rental_agen_is_acti_0a7e72_idx",
		),
		migrations.RemoveField(model_name="rentalagent", name="address"),
		migrations.RemoveField(model_name="rentalagent", name="email"),
		migrations.RemoveField(model_name="rentalagent", name="name"),
		migrations.RemoveField(model_name="rentalagent", name="phone"),
		migrations.AddIndex(
			model_name="rentalagent",
			index=models.Index(fields=["is_active", "contact"], name="rental_agen_is_acti_contact_idx"),
		),
		migrations.AlterModelOptions(
			name="rentalagent",
			options={"ordering": ("contact__display_name",)},
		),
	]
