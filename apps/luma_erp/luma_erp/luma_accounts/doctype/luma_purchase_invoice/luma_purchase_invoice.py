import frappe
from frappe.model.document import Document

from luma_erp.luma_accounts.accounting import cancel_entry, create_invoice_entry


class LumaPurchaseInvoice(Document):
	def validate(self) -> None:
		if not self.items:
			frappe.throw("A purchase invoice must contain at least one item.")

		self.total_amount = 0
		for item in self.items:
			if item.qty <= 0:
				frappe.throw("Invoice item quantity must be greater than zero.")
			if item.rate < 0:
				frappe.throw("Invoice item rate cannot be negative.")

			item.amount = item.qty * item.rate
			self.total_amount += item.amount

		if self.purchase_receipt:
			self._validate_purchase_receipt()

	def before_insert(self) -> None:
		self.status = "Draft"
		self.currency = self.currency or "USD"
		self.outstanding_amount = 0

	def on_submit(self) -> None:
		self.outstanding_amount = self.total_amount
		self.status = "Submitted"
		self._update_receipt_quantities(1)
		self.journal_entry = create_invoice_entry(self, "purchase")

	def before_submit(self) -> None:
		self.outstanding_amount = self.total_amount
		self.status = "Submitted"

	def on_cancel(self) -> None:
		self._update_receipt_quantities(-1)
		cancel_entry(self.journal_entry)
		self.outstanding_amount = 0
		self.status = "Cancelled"

	def _validate_purchase_receipt(self) -> None:
		receipt = frappe.get_doc("Luma Purchase Receipt", self.purchase_receipt)
		if receipt.status != "Submitted":
			frappe.throw("A purchase invoice requires a submitted purchase receipt.")
		if receipt.supplier != self.supplier or receipt.organization != self.organization:
			frappe.throw("Invoice supplier and organization must match the purchase receipt.")

		for invoice_item in self.items:
			received_qty = sum(
				receipt_item.qty - (receipt_item.invoiced_qty or 0)
				for receipt_item in receipt.items
				if receipt_item.item == invoice_item.item
			)
			if invoice_item.qty > received_qty:
				frappe.throw(
					f"Invoice quantity for {invoice_item.item} exceeds the uninvoiced receipt quantity."
				)

	def _update_receipt_quantities(self, direction: int) -> None:
		if not self.purchase_receipt:
			return
		receipt = frappe.get_doc("Luma Purchase Receipt", self.purchase_receipt)
		for invoice_item in self.items:
			for receipt_item in receipt.items:
				if receipt_item.item == invoice_item.item:
					receipt_item.db_set(
						"invoiced_qty",
						(receipt_item.invoiced_qty or 0) + direction * invoice_item.qty,
					)
					break
