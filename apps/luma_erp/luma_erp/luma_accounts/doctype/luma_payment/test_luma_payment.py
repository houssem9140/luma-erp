import frappe
from frappe.tests.utils import FrappeTestCase


class TestLumaPayment(FrappeTestCase):
	def _create_invoice(self) -> str:
		invoice = frappe.get_doc(
			{
				"doctype": "Luma Sales Invoice",
				"customer": "CUST001",
				"organization": "Demo Organization",
				"currency": "USD",
				"items": [{"item": "ITEM001", "qty": 2, "rate": 25}],
			}
		).insert(ignore_permissions=True, ignore_links=True)
		invoice.submit()
		return invoice.name

	def test_partial_payment_updates_outstanding_amount(self) -> None:
		invoice_name = self._create_invoice()
		payment = frappe.get_doc(
			{
				"doctype": "Luma Payment",
				"payment_type": "Receive",
				"organization": "Demo Organization",
				"currency": "USD",
				"amount": 25,
				"reference_doctype": "Luma Sales Invoice",
				"reference_name": invoice_name,
			}
		)
		payment.validate()
		payment.on_submit()

		invoice = frappe.get_doc("Luma Sales Invoice", invoice_name)
		self.assertEqual(invoice.outstanding_amount, 25)
		self.assertEqual(invoice.status, "Partially Paid")

	def test_payment_cannot_exceed_outstanding_amount(self) -> None:
		invoice_name = self._create_invoice()
		payment = frappe.get_doc(
			{
				"doctype": "Luma Payment",
				"payment_type": "Receive",
				"organization": "Demo Organization",
				"currency": "USD",
				"amount": 51,
				"reference_doctype": "Luma Sales Invoice",
				"reference_name": invoice_name,
			}
		)

		with self.assertRaises(frappe.ValidationError):
			payment.validate()

	def test_payments_require_matching_invoice_type(self) -> None:
		payment = frappe.get_doc(
			{
				"doctype": "Luma Payment",
				"payment_type": "Pay",
				"organization": "Demo Organization",
				"currency": "USD",
				"amount": 10,
				"reference_doctype": "Luma Sales Invoice",
				"reference_name": "SI-00001",
			}
		)

		with self.assertRaises(frappe.ValidationError):
			payment.validate()

	def test_cancel_reverses_payment_allocation(self) -> None:
		invoice_name = self._create_invoice()
		payment = frappe.get_doc(
			{
				"doctype": "Luma Payment",
				"payment_type": "Receive",
				"organization": "Demo Organization",
				"currency": "USD",
				"amount": 25,
				"reference_doctype": "Luma Sales Invoice",
				"reference_name": invoice_name,
			}
		)
		payment.validate()
		payment.on_submit()
		payment.on_cancel()

		invoice = frappe.get_doc("Luma Sales Invoice", invoice_name)
		self.assertEqual(invoice.outstanding_amount, 50)
		self.assertEqual(invoice.status, "Submitted")
