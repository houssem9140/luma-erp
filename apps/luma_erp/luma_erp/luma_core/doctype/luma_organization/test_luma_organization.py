import frappe
from frappe.tests.utils import FrappeTestCase


class TestLumaOrganization(FrappeTestCase):
	def test_code_rejects_punctuation(self) -> None:
		organization = frappe.get_doc(
			{
				"doctype": "Luma Organization",
				"organization_name": "Demo Organization",
				"organization_code": " demo-01 ",
				"default_currency": "USD",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			organization.insert()
