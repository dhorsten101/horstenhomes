from django.test import TestCase

from apps.contacts.forms import ContactForm


class ContactFormTests(TestCase):
	def test_contact_form_accepts_valid_tags_json(self):
		form = ContactForm(
			data={
				"display_name": "John Doe",
				"email": "john@example.com",
				"phone": "",
				"tags": '["owner","vip"]',
			}
		)
		self.assertTrue(form.is_valid(), form.errors.as_json())

		obj = form.save()
		self.assertEqual(obj.display_name, "John Doe")
		self.assertEqual(obj.tags, ["owner", "vip"])

	def test_contact_form_rejects_invalid_tags_json(self):
		form = ContactForm(
			data={
				"display_name": "Jane",
				"tags": "{not-json}",
			}
		)
		self.assertFalse(form.is_valid())
		self.assertIn("tags", form.errors)
