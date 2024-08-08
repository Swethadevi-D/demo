# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _, qb, scrub
from frappe.utils import getdate, nowdate


class PartyLedgerSummaryReport:
	def __init__(self, filters=None):
		self.filters = frappe._dict(filters or {})
		self.filters.from_date = getdate(self.filters.from_date or nowdate())
		self.filters.to_date = getdate(self.filters.to_date or nowdate())

		if not self.filters.get("company"):
			self.filters["company"] = frappe.db.get_single_value("Global Defaults", "default_company")

	def run(self, args):
		if self.filters.from_date > self.filters.to_date:
			frappe.throw(_("From Date must be before To Date"))

		self.filters.party_type = args.get("party_type")
		self.party_naming_by = frappe.db.get_value(args.get("naming_by")[0], None, args.get("naming_by")[1])

		self.get_gl_entries()
		self.get_additional_columns()
		self.get_return_invoices()
		self.get_party_adjustment_amounts()

		columns = self.get_columns()
		data = self.get_data()
		return columns, data

	def get_additional_columns(self):
		"""
		Additional Columns for 'User Permission' based access control
		"""

		if self.filters.party_type == "Customer":
			self.territories = frappe._dict({})
			self.customer_group = frappe._dict({})

			customer = qb.DocType("Customer")
			result = (
				frappe.qb.from_(customer)
				.select(
					customer.name, customer.territory, customer.customer_group, customer.default_sales_partner
				)
				.where(customer.disabled == 0)
				.run(as_dict=True)
			)

			for x in result:
				self.territories[x.name] = x.territory
				self.customer_group[x.name] = x.customer_group
		else:
			self.supplier_group = frappe._dict({})
			supplier = qb.DocType("Supplier")
			result = (
				frappe.qb.from_(supplier)
				.select(supplier.name, supplier.supplier_group)
				.where(supplier.disabled == 0)
				.run(as_dict=True)
			)

			for x in result:
				self.supplier_group[x.name] = x.supplier_group

	def get_columns(self):
		columns = [
			{
				"label": _(self.filters.party_type),
				"fieldtype": "Link",
				"fieldname": "party",
				"options": self.filters.party_type,
				"width": 200,
			}
		]

		if self.party_naming_by == "Naming Series":
			columns.append(
				{
					"label": _(self.filters.party_type + "Name"),
					"fieldtype": "Data",
					"fieldname": "party_name",
					"width": 110,
				}
			)

		credit_or_debit_note = "Credit Note" if self.filters.party_type == "Customer" else "Debit Note"

		columns += [
			{
				"label": _("Opening Balance"),
				"fieldname": "opening_balance",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _("Invoiced Amount"),
				"fieldname": "invoiced_amount",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _("Paid Amount"),
				"fieldname": "paid_amount",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _(credit_or_debit_note),
				"fieldname": "return_amount",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
		]

		for account in self.party_adjustment_accounts:
			columns.append(
				{
					"label": account,
					"fieldname": "adj_" + scrub(account),
					"fieldtype": "Currency",
					"options": "currency",
					"width": 120,
					"is_adjustment": 1,
				}
			)

		columns += [
			{
				"label": _("Closing Balance"),
				"fieldname": "closing_balance",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _("Currency"),
				"fieldname": "currency",
				"fieldtype": "Link",
				"options": "Currency",
				"width": 50,
			},
		]

		# Hidden columns for handling 'User Permissions'
		if self.filters.party_type == "Customer":
			columns += [
				{
					"label": _("Territory"),
					"fieldname": "territory",
					"fieldtype": "Link",
					"options": "Territory",
					"hidden": 1,
				},
				{
					"label": _("Customer Group"),
					"fieldname": "customer_group",
					"fieldtype": "Link",
					"options": "Customer Group",
					"hidden": 1,
				},
			]
		else:
			columns += [
				{
					"label": _("Supplier Group"),
					"fieldname": "supplier_group",
					"fieldtype": "Link",
					"options": "Supplier Group",
					"hidden": 1,
				}
			]

		return columns

	def get_data(self):
		company_currency = frappe.get_cached_value("Company", self.filters.get("company"), "default_currency")
		invoice_dr_or_cr = "debit" if self.filters.party_type == "Customer" else "credit"
		reverse_dr_or_cr = "credit" if self.filters.party_type == "Customer" else "debit"

		self.party_data = frappe._dict({})
		for gle in self.gl_entries:
			self.party_data.setdefault(
				gle.party,
				frappe._dict(
					{
						"party": gle.party,
						"party_name": gle.party_name,
						"opening_balance": 0,
						"invoiced_amount": 0,
						"paid_amount": 0,
						"return_amount": 0,
						"closing_balance": 0,
						"currency": company_currency,
					}
				),
			)

			if self.filters.party_type == "Customer":
				self.party_data[gle.party].update({"territory": self.territories.get(gle.party)})
				self.party_data[gle.party].update({"customer_group": self.customer_group.get(gle.party)})
			else:
				self.party_data[gle.party].update({"supplier_group": self.supplier_group.get(gle.party)})

			amount = gle.get(invoice_dr_or_cr) - gle.get(reverse_dr_or_cr)
			self.party_data[gle.party].closing_balance += amount

			if gle.posting_date < self.filters.from_date or gle.is_opening == "Yes":
				self.party_data[gle.party].opening_balance += amount
			else:
				if amount > 0:
					self.party_data[gle.party].invoiced_amount += amount
				elif gle.voucher_no in self.return_invoices:
					self.party_data[gle.party].return_amount -= amount
				else:
					self.party_data[gle.party].paid_amount -= amount

		out = []
		for party, row in self.party_data.items():
			if (
				row.opening_balance
				or row.invoiced_amount
				or row.paid_amount
				or row.return_amount
				or row.closing_balance  # changed this line to 'closing_balance' from 'closing_amount'
			):
				total_party_adjustment = sum(
					amount for amount in self.party_adjustment_details.get(party, {}).values()
				)
				row.paid_amount -= total_party_adjustment

				adjustments = self.party_adjustment_details.get(party, {})
				for account in self.party_adjustment_accounts:
					row["adj_" + scrub(account)] = adjustments.get(account, 0)

				# Only append rows with a non-zero closing balance
				if row.closing_balance != 0:
					out.append(row)

		return out

	def get_gl_entries(self):
		conditions = self.prepare_conditions()
		join = join_field = ""
		if self.filters.party_type == "Customer":
			join_field = ", p.customer_name as party_name"
			join = "left join `tabCustomer` p on gle.party = p.name"
		elif self.filters.party_type == "Supplier":
			join_field = ", p.supplier_name as party_name"
			join = "left join `tabSupplier` p on gle.party = p.name"

		self.gl_entries = frappe.db.sql(
			f"""
			select
				gle.posting_date, gle.party, gle.voucher_type, gle.voucher_no, gle.against_voucher_type,
				gle.against_voucher, gle.is_opening, gle.debit, gle.credit {join_field}
			from `tabGL Entry` gle {join}
			where
				gle.docstatus < 2 and gle.is_cancelled = 0 and gle.party_type=%(party_type)s and gle.party is not null
				{conditions}
			order by gle.party, gle.posting_date
		""",
			self.filters,
			as_dict=1,
		)

	def prepare_conditions(self):
		conditions = []

		for opts in (
			("company", " and gle.company=%(company)s"),
			("finance_book", " and gle.finance_book=%(finance_book)s"),
			("from_date", " and gle.posting_date >=%(from_date)s"),
			("to_date", " and gle.posting_date <=%(to_date)s"),
			("party", " and gle.party =%(party)s"),
		):
			if self.filters.get(opts[0]):
				conditions.append(opts[1])

		return " ".join(conditions)

	def get_return_invoices(self):
		doctype = "Sales Invoice" if self.filters.party_type == "Customer" else "Purchase Invoice"
		self.return_invoices = [x.name for x in frappe.get_all(doctype, filters={"is_return": 1})]

	def get_party_adjustment_amounts(self):
		adjustment_filters = {"docstatus": 1, "account": ["in", self.party_adjustment_accounts]}
		conditions = []

		if self.filters.get("company"):
			conditions.append("company=%(company)s")
			adjustment_filters["company"] = self.filters.get("company")

		if self.filters.get("party"):
			conditions.append("party_type=%(party_type)s and party=%(party)s")
			adjustment_filters.update({"party_type": self.filters.party_type, "party": self.filters.party})
		else:
			conditions.append("party_type=%(party_type)s")
			adjustment_filters.update({"party_type": self.filters.party_type})

		if self.filters.get("finance_book"):
			adjustment_filters["finance_book"] = self.filters.get("finance_book")

		accounts = ",".join([frappe.db.escape(account) for account in self.party_adjustment_accounts])

		account_conditions = f"""account in ({accounts})"""

		self.party_adjustment_details = frappe._dict({})
		for gle in frappe.get_all(
			"GL Entry",
			fields=["party", "account", "sum(debit - credit) as amount"],
			filters=adjustment_filters,
			group_by="party, account",
			conditions=conditions,
		):
			self.party_adjustment_details.setdefault(gle.party, frappe._dict({})).setdefault(gle.account, gle.amount)
