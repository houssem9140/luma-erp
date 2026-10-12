import frappe
from frappe.model.document import Document

from luma_erp.luma_accounts.accounting import cancel_entry, create_invoice_entry


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

		if self.delivery_note:
			self._validate_delivery_note()

	def before_insert(self) -> None:
		self.status = "Draft"
		self.currency = self.currency or "USD"
		self.outstanding_amount = 0

	def on_submit(self) -> None:
		self.outstanding_amount = self.total_amount
		self.status = "Submitted"
		self._update_delivery_quantities(1)
		self.journal_entry = create_invoice_entry(self, "sales")

	def before_submit(self) -> None:
		self.outstanding_amount = self.total_amount
		self.status = "Submitted"

	def on_cancel(self) -> None:
		self._update_delivery_quantities(-1)
		cancel_entry(self.journal_entry)
		self.outstanding_amount = 0
		self.status = "Cancelled"

	def _validate_delivery_note(self) -> None:
		delivery = frappe.get_doc("Luma Delivery Note", self.delivery_note)
		if delivery.status != "Submitted":
			frappe.throw("A sales invoice requires a submitted delivery note.")
		if delivery.customer != self.customer or delivery.organization != self.organization:
			frappe.throw("Invoice customer and organization must match the delivery note.")

		for invoice_item in self.items:
			delivered_qty = sum(
				delivery_item.qty - (delivery_item.invoiced_qty or 0)
				for delivery_item in delivery.items
				if delivery_item.item == invoice_item.item
			)
			if invoice_item.qty > delivered_qty:
				frappe.throw(
					f"Invoice quantity for {invoice_item.item} exceeds the uninvoiced delivery quantity."
				)

	def _update_delivery_quantities(self, direction: int) -> None:
		if not self.delivery_note:
			return
		delivery = frappe.get_doc("Luma Delivery Note", self.delivery_note)
		for invoice_item in self.items:
			for delivery_item in delivery.items:
				if delivery_item.item == invoice_item.item:
					delivery_item.db_set(
						"invoiced_qty",
						(delivery_item.invoiced_qty or 0) + direction * invoice_item.qty,
					)
					break
