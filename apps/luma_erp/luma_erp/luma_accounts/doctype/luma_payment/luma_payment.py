import frappe
from frappe.model.document import Document

from luma_erp.luma_accounts.accounting import cancel_entry, create_payment_entry


class LumaPayment(Document):
	def validate(self) -> None:
		if self.amount <= 0:
			frappe.throw("Payment amount must be greater than zero.")

		if self.payment_type == "Receive" and self.reference_doctype != "Luma Sales Invoice":
			frappe.throw("Receive payments must reference a sales invoice.")
		if self.payment_type == "Pay" and self.reference_doctype != "Luma Purchase Invoice":
			frappe.throw("Pay payments must reference a purchase invoice.")
		if not self.reference_name:
			frappe.throw("A payment invoice reference is required.")

		invoice = frappe.get_doc(self.reference_doctype, self.reference_name)
		if invoice.status != "Submitted":
			frappe.throw("Payments can only be allocated to submitted invoices.")
		if self.amount > invoice.outstanding_amount:
			frappe.throw("Payment amount cannot exceed the invoice outstanding amount.")
		if (self.currency or "USD") != (invoice.currency or "USD"):
			frappe.throw("Payment currency must match the invoice currency.")

	def before_insert(self) -> None:
		self.status = "Draft"

	def on_submit(self) -> None:
		invoice = frappe.get_doc(self.reference_doctype, self.reference_name)
		invoice.outstanding_amount -= self.amount
		invoice.status = "Paid" if invoice.outstanding_amount == 0 else "Partially Paid"
		invoice.db_set(
			{
				"outstanding_amount": invoice.outstanding_amount,
				"status": invoice.status,
			},
			update_modified=True,
		)
		self.journal_entry = create_payment_entry(self)
		self.db_set(
			{"status": "Submitted", "journal_entry": self.journal_entry},
			update_modified=True,
		)

	def on_cancel(self) -> None:
		invoice = frappe.get_doc(self.reference_doctype, self.reference_name)
		invoice.outstanding_amount += self.amount
		invoice.status = "Submitted"
		invoice.db_set(
			{
				"outstanding_amount": invoice.outstanding_amount,
				"status": invoice.status,
			},
			update_modified=True,
		)
		cancel_entry(self.journal_entry)
		self.db_set("status", "Cancelled", update_modified=True)
