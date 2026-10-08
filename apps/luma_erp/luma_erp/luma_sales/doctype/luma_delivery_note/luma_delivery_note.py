import frappe
from frappe.model.document import Document


class LumaDeliveryNote(Document):
	def validate(self) -> None:
		if not self.items:
			frappe.throw("A delivery note must contain at least one item.")
		if not self.warehouse:
			frappe.throw("A delivery note requires a warehouse.")
		if self.sales_order:
			order = frappe.get_doc("Luma Sales Order", self.sales_order)
			if order.customer != self.customer or order.organization != self.organization:
				frappe.throw("Delivery customer and organization must match the sales order.")

		for item in self.items:
			if item.qty <= 0:
				frappe.throw("Delivery quantity must be greater than zero.")
			if self.sales_order:
				ordered_qty = sum(
					order_item.qty - (order_item.delivered_qty or 0)
					for order_item in order.items
					if order_item.item == item.item
				)
				if item.qty > ordered_qty:
					frappe.throw(
						f"Delivery quantity for {item.item} exceeds the sales order."
					)

	def before_insert(self) -> None:
		self.status = "Draft"

	def on_submit(self) -> None:
		movement = frappe.get_doc(
			{
				"doctype": "Luma Stock Entry",
				"entry_type": "Issue",
				"organization": self.organization,
				"source_warehouse": self.warehouse,
				"items": [
					{"item": item.item, "qty": item.qty, "uom": item.uom}
					for item in self.items
				],
			}
		)
		movement.insert(ignore_permissions=True, ignore_links=True)
		movement.flags.ignore_links = True
		movement.submit()
		self._update_order_quantities(1)
		self.db_set({"stock_entry": movement.name, "status": "Submitted"})

	def on_cancel(self) -> None:
		if self.stock_entry:
			movement = frappe.get_doc("Luma Stock Entry", self.stock_entry)
			if movement.docstatus == 1:
				movement.cancel()
		self._update_order_quantities(-1)
		self.db_set({"status": "Cancelled"})

	def _update_order_quantities(self, direction: int) -> None:
		if not self.sales_order:
			return
		order = frappe.get_doc("Luma Sales Order", self.sales_order)
		for delivery_item in self.items:
			for order_item in order.items:
				if order_item.item == delivery_item.item:
					order_item.db_set(
						"delivered_qty",
						(order_item.delivered_qty or 0) + direction * delivery_item.qty,
					)
					break
