import frappe
from frappe.tests.utils import FrappeTestCase


class TestLumaPurchaseReceipt(FrappeTestCase):
	def test_submit_creates_receipt_stock(self) -> None:
		suffix = frappe.generate_hash(length=8).upper()
		organization, item, supplier, warehouse = self._create_setup(suffix)
		order = frappe.get_doc(
			{
				"doctype": "Luma Purchase Order",
				"supplier": supplier,
				"organization": organization,
				"items": [{"item": item, "qty": 4, "rate": 8}],
			}
		).insert(ignore_permissions=True)
		receipt = frappe.get_doc(
			{
				"doctype": "Luma Purchase Receipt",
				"supplier": supplier,
				"organization": organization,
				"purchase_order": order.name,
				"warehouse": warehouse,
				"items": [{"item": item, "qty": 4}],
			}
		).insert(ignore_permissions=True, ignore_links=True)

		receipt.submit()

		self.assertEqual(receipt.status, "Submitted")
		self.assertEqual(
			frappe.db.get_value(
				"Luma Stock Balance",
				{"item": item, "warehouse": warehouse},
				"quantity",
			),
			4,
		)

	def _create_setup(self, suffix: str) -> tuple[str, str, str, str]:
		organization = frappe.get_doc(
			{
				"doctype": "Luma Organization",
				"organization_name": f"Receipt Org {suffix}",
				"organization_code": f"RORG{suffix}",
				"default_currency": "USD",
			}
		).insert(ignore_permissions=True)
		item = frappe.get_doc(
			{
				"doctype": "Luma Item",
				"item_code": f"RITEM{suffix}",
				"item_name": "Receipt Test Item",
				"item_group": "Test",
			}
		).insert(ignore_permissions=True)
		supplier = frappe.get_doc(
			{
				"doctype": "Luma Supplier",
				"supplier_name": f"Receipt Supplier {suffix}",
				"supplier_code": f"RSUPP{suffix}",
				"organization": organization.name,
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Luma Warehouse",
				"warehouse_code": f"PR{suffix}",
				"warehouse_name": "Receipt Test Warehouse",
				"organization": organization.name,
			}
		).insert(ignore_permissions=True)
		return organization.name, item.name, supplier.name, f"PR{suffix}"
