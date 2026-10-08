import frappe
from frappe.tests.utils import FrappeTestCase


class TestLumaWarehouse(FrappeTestCase):
	def test_code_is_normalized(self) -> None:
		warehouse = frappe.get_doc(
			{
				"doctype": "Luma Warehouse",
				"warehouse_code": "main01",
				"warehouse_name": "Main Warehouse",
				"organization": "Demo Organization",
			}
		)
		warehouse.validate()
		self.assertEqual(warehouse.warehouse_code, "MAIN01")
