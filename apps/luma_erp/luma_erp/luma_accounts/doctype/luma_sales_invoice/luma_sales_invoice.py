import frappe
from frappe.model.document import Document


class LumaSalesInvoice(Document):
	def validate(self) -> None:
		if not self.items:
			frappe.throw("A sales invoice must contain at least one item.")

		self.total_amount = 0
		for item in self.items:
			if item.qty <= 0:
				frappe.throw("Invoice item quantity must be greater than zero.")
			if item.rate < 0:
				frappe.throw("Invoice item rate cannot be negative.")

			item.amount = item.qty * item.rate
			self.total_amount += item.amount

	def before_insert(self) -> None:
		self.status = "Draft"
		self.outstanding_amount = 0

	def on_submit(self) -> None:
		self.outstanding_amount = self.total_amount
		self.status = "Submitted"

	def on_cancel(self) -> None:
		self.outstanding_amount = 0
		self.status = "Cancelled"
