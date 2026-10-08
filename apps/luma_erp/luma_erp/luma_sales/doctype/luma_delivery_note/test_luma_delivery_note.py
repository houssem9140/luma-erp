import frappe
from frappe.tests.utils import FrappeTestCase


class TestLumaDeliveryNote(FrappeTestCase):
	def test_repeated_delivery_cannot_exceed_order(self) -> None:
		suffix = frappe.generate_hash(length=8).upper()
		organization, item, customer, warehouse = self._create_setup(suffix)
		order = frappe.get_doc(
			{
				"doctype": "Luma Sales Order",
				"customer": customer,
				"organization": organization,
				"items": [{"item": item, "qty": 2, "rate": 10}],
			}
		).insert(ignore_permissions=True)
		first_delivery = frappe.get_doc(
			{
				"doctype": "Luma Delivery Note",
				"customer": customer,
				"organization": organization,
				"sales_order": order.name,
				"warehouse": warehouse,
				"items": [{"item": item, "qty": 2}],
			}
		).insert(ignore_permissions=True, ignore_links=True)
		first_delivery.submit()
		second_delivery = frappe.get_doc(
			{
				"doctype": "Luma Delivery Note",
				"customer": customer,
				"organization": organization,
				"sales_order": order.name,
				"warehouse": warehouse,
				"items": [{"item": item, "qty": 1}],
			}
		)

		with self.assertRaises(frappe.ValidationError):
			second_delivery.validate()

	def test_submit_creates_issue_and_cancel_reverses_it(self) -> None:
		suffix = frappe.generate_hash(length=8).upper()
		organization, item, customer, warehouse = self._create_setup(suffix)
		order = frappe.get_doc(
			{
				"doctype": "Luma Sales Order",
				"customer": customer,
				"organization": organization,
				"items": [{"item": item, "qty": 2, "rate": 10}],
			}
		).insert(ignore_permissions=True)
		delivery = frappe.get_doc(
			{
				"doctype": "Luma Delivery Note",
				"customer": customer,
				"organization": organization,
				"sales_order": order.name,
				"warehouse": warehouse,
				"items": [{"item": item, "qty": 2}],
			}
		).insert(ignore_permissions=True, ignore_links=True)

		delivery.submit()

		self.assertEqual(delivery.status, "Submitted")
		self.assertEqual(
			frappe.db.get_value(
				"Luma Sales Order Item",
				{"parent": order.name},
				"delivered_qty",
			),
			2,
		)
		self.assertEqual(
			frappe.db.get_value(
				"Luma Stock Balance",
				{"item": item, "warehouse": warehouse},
				"quantity",
			),
			0,
		)

		delivery.cancel()

		self.assertEqual(delivery.status, "Cancelled")
		self.assertEqual(
			frappe.db.get_value(
				"Luma Sales Order Item",
				{"parent": order.name},
				"delivered_qty",
			),
			0,
		)
		self.assertEqual(
			frappe.db.get_value(
				"Luma Stock Balance",
				{"item": item, "warehouse": warehouse},
				"quantity",
			),
			2,
		)

	def _create_setup(self, suffix: str) -> tuple[str, str, str, str]:
		organization = frappe.get_doc(
			{
				"doctype": "Luma Organization",
				"organization_name": f"Delivery Org {suffix}",
				"organization_code": f"DORG{suffix}",
				"default_currency": "USD",
			}
		).insert(ignore_permissions=True)
		item = frappe.get_doc(
			{
				"doctype": "Luma Item",
				"item_code": f"DITEM{suffix}",
				"item_name": "Delivery Test Item",
				"item_group": "Test",
			}
		).insert(ignore_permissions=True)
		customer = frappe.get_doc(
			{
				"doctype": "Luma Customer",
				"customer_name": f"Delivery Customer {suffix}",
				"customer_code": f"DCUST{suffix}",
				"organization": organization.name,
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Luma Warehouse",
				"warehouse_code": f"DN{suffix}",
				"warehouse_name": "Delivery Test Warehouse",
				"organization": organization.name,
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Luma Stock Balance",
				"item": item.name,
				"warehouse": f"DN{suffix}",
				"organization": organization.name,
				"quantity": 2,
			}
		).insert(ignore_permissions=True)
		return organization.name, item.name, customer.name, f"DN{suffix}"
