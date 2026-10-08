import frappe
from frappe.model.document import Document


class LumaPurchaseReceipt(Document):
	def validate(self) -> None:
		if not self.items:
			frappe.throw("A purchase receipt must contain at least one item.")
		if not self.warehouse:
			frappe.throw("A purchase receipt requires a warehouse.")

		for item in self.items:
			if item.qty <= 0:
				frappe.throw("Receipt quantity must be greater than zero.")

	def before_insert(self) -> None:
		self.status = "Draft"

	def on_submit(self) -> None:
		movement = frappe.get_doc(
			{
				"doctype": "Luma Stock Entry",
				"entry_type": "Receipt",
				"organization": self.organization,
				"target_warehouse": self.warehouse,
				"items": [
					{"item": item.item, "qty": item.qty, "uom": item.uom}
					for item in self.items
				],
			}
		)
		movement.insert(ignore_permissions=True, ignore_links=True)
		movement.flags.ignore_links = True
		movement.submit()
		self.db_set({"stock_entry": movement.name, "status": "Submitted"})

	def on_cancel(self) -> None:
		if self.stock_entry:
			movement = frappe.get_doc("Luma Stock Entry", self.stock_entry)
			if movement.docstatus == 1:
				movement.cancel()
		self.db_set({"status": "Cancelled"})
