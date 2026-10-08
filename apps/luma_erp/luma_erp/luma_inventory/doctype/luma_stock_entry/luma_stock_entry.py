import frappe
from frappe.model.document import Document


class LumaStockEntry(Document):
	def validate(self) -> None:
		if not self.items:
			frappe.throw("A stock entry must contain at least one item.")

		if self.entry_type == "Receipt" and self.source_warehouse:
			frappe.throw("A receipt cannot have a source warehouse.")
		if self.entry_type == "Issue" and self.target_warehouse:
			frappe.throw("An issue cannot have a target warehouse.")
		if self.entry_type == "Transfer" and (
			not self.source_warehouse or not self.target_warehouse
		):
			frappe.throw("A transfer requires source and target warehouses.")
		if (
			self.entry_type == "Transfer"
			and self.source_warehouse
			and self.source_warehouse == self.target_warehouse
		):
			frappe.throw("Source and target warehouses must be different.")

		self.total_quantity = 0
		for item in self.items:
			if item.qty <= 0:
				frappe.throw("Stock quantity must be greater than zero.")
			self.total_quantity += item.qty

	def before_insert(self) -> None:
		self.status = "Draft"
