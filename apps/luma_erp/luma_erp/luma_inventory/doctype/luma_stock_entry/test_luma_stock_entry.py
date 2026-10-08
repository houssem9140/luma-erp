import frappe
from frappe.tests.utils import FrappeTestCase


class TestLumaStockEntry(FrappeTestCase):
	def _create_stock_setup(self) -> tuple[str, str, str]:
		suffix = frappe.generate_hash(length=8).upper()
		organization = frappe.get_doc(
			{
				"doctype": "Luma Organization",
				"organization_name": f"Stock Test {suffix}",
				"organization_code": f"ORG{suffix}",
				"default_currency": "USD",
			}
		).insert(ignore_permissions=True)
		item = frappe.get_doc(
			{
				"doctype": "Luma Item",
				"item_code": f"STOCK{suffix}",
				"item_name": "Stock Test Item",
				"item_group": "Test",
			}
		).insert(ignore_permissions=True)
		warehouse = frappe.get_doc(
			{
				"doctype": "Luma Warehouse",
				"warehouse_code": f"WH{suffix}",
				"warehouse_name": "Stock Test Warehouse",
				"organization": organization.name,
			}
		).insert(ignore_permissions=True)
		return organization.name, item.name, warehouse.name

	def test_receipt_total_is_calculated(self) -> None:
		entry = frappe.get_doc(
			{
				"doctype": "Luma Stock Entry",
				"entry_type": "Receipt",
				"organization": "Demo Organization",
				"target_warehouse": "MAIN01",
				"items": [{"item": "ITEM001", "qty": 5}],
			}
		)

		entry.validate()

		self.assertEqual(entry.total_quantity, 5)

	def test_transfer_requires_two_warehouses(self) -> None:
		entry = frappe.get_doc(
			{
				"doctype": "Luma Stock Entry",
				"entry_type": "Transfer",
				"organization": "Demo Organization",
				"items": [{"item": "ITEM001", "qty": 1}],
			}
		)

		with self.assertRaises(frappe.ValidationError):
			entry.validate()

	def test_zero_quantity_is_rejected(self) -> None:
		entry = frappe.get_doc(
			{
				"doctype": "Luma Stock Entry",
				"entry_type": "Issue",
				"organization": "Demo Organization",
				"source_warehouse": "MAIN01",
				"items": [{"item": "ITEM001", "qty": 0}],
			}
		)

		with self.assertRaises(frappe.ValidationError):
			entry.validate()

	def test_submit_updates_and_cancel_reverses_balance(self) -> None:
		organization, item, warehouse = self._create_stock_setup()
		entry = frappe.get_doc(
			{
				"doctype": "Luma Stock Entry",
				"entry_type": "Receipt",
				"organization": organization,
				"target_warehouse": warehouse,
				"items": [{"item": item, "qty": 5}],
			}
		).insert(ignore_permissions=True)

		entry.submit()

		self.assertEqual(
			frappe.db.get_value(
				"Luma Stock Balance",
				{"item": item, "warehouse": warehouse, "organization": organization},
				"quantity",
			),
			5,
		)

		entry.cancel()

		self.assertEqual(
			frappe.db.get_value(
				"Luma Stock Balance",
				{"item": item, "warehouse": warehouse, "organization": organization},
				"quantity",
			),
			0,
		)
