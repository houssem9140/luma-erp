import frappe
from frappe.tests.utils import FrappeTestCase


class TestLumaCustomer(FrappeTestCase):
	def test_code_is_normalized(self) -> None:
		customer = frappe.get_doc(
			{
				"doctype": "Luma Customer",
				"customer_name": "Demo Customer",
				"customer_code": "customer01",
				"customer_type": "Company",
				"organization": "Demo Organization",
			}
		)
		customer.validate()
		self.assertEqual(customer.customer_code, "CUSTOMER01")
