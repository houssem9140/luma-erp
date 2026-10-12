import frappe
from frappe.tests.utils import FrappeTestCase

from luma_erp.demo import seed_demo_data


class TestLumaDemoData(FrappeTestCase):
	def test_seed_demo_data_is_idempotent(self) -> None:
		first = seed_demo_data()
		second = seed_demo_data()

		self.assertEqual(first, second)
		self.assertTrue(frappe.db.exists("Luma Organization", first["organization"]))
		self.assertTrue(frappe.db.exists("Luma Customer", first["customer"]))
		self.assertTrue(frappe.db.exists("Luma Supplier", first["supplier"]))
		self.assertTrue(frappe.db.exists("Luma Item", first["item"]))
		self.assertTrue(frappe.db.exists("Luma Warehouse", first["warehouse"]))
