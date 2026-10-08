import frappe
from frappe.tests.utils import FrappeTestCase


class TestLumaSupplier(FrappeTestCase):
	def test_code_rejects_punctuation(self) -> None:
		supplier = frappe.get_doc(
			{
				"doctype": "Luma Supplier",
				"supplier_name": "Demo Supplier",
				"supplier_code": "supplier-01",
				"organization": "Demo Organization",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			supplier.validate()
