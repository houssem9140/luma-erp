import frappe
from frappe.model.document import Document


class LumaCustomer(Document):
	def validate(self) -> None:
		self.customer_code = self.customer_code.strip().upper()
		self.customer_name = self.customer_name.strip()

		if not self.customer_code.isalnum():
			frappe.throw("Customer Code must contain only letters and numbers.")
