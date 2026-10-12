import frappe
from frappe.model.document import Document


class LumaJournalEntry(Document):
	def validate(self) -> None:
		if not self.accounts:
			frappe.throw("A journal entry must contain at least one account.")

		self.total_debit = 0
		self.total_credit = 0
		for account in self.accounts:
			debit = account.debit or 0
			credit = account.credit or 0
			if debit < 0 or credit < 0:
				frappe.throw("Journal amounts cannot be negative.")
			if debit and credit:
				frappe.throw("A journal line cannot contain both debit and credit.")
			if not debit and not credit:
				frappe.throw("A journal line must contain a debit or credit amount.")
			self.total_debit += debit
			self.total_credit += credit

		if self.total_debit != self.total_credit:
			frappe.throw("Journal entry debits and credits must be balanced.")

	def before_insert(self) -> None:
		self.status = "Draft"
		self.currency = self.currency or "USD"

	def before_submit(self) -> None:
		self.validate()
		self.status = "Submitted"

	def on_cancel(self) -> None:
		self.status = "Cancelled"
