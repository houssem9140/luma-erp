import frappe
from frappe.model.document import Document


class LumaSalesOrder(Document):
	def validate(self) -> None:
		if not self.items:
			frappe.throw("A sales order must contain at least one item.")

		self.total_amount = 0
		for item in self.items:
			if item.qty <= 0:
				frappe.throw("Item quantity must be greater than zero.")
			if item.rate < 0:
				frappe.throw("Item rate cannot be negative.")

			item.amount = item.qty * item.rate
			self.total_amount += item.amount

	def before_insert(self) -> None:
		self.status = "Draft"
