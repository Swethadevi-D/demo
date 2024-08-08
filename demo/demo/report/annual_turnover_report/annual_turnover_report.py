from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils.data import flt

def execute(filters=None):
    columns = []
    data = []

    if not filters:
        filters = {}

    party_type = filters.get('party_type')
    party = filters.get('party')

    # if party_type not in ['Customer', 'Supplier']:
    #     frappe.throw(_("Invalid Party Type. Please select either 'Customer' or 'Supplier'."))

    if party_type == 'Customer':
        columns = [
            _("Customer Name") + "::150",
            _("Annual Billing Amount") + ":Currency:150",
            _("Outstanding Amount") + ":Currency:150",
            _("Total Quantity") + ":Float:150",
            _("Total Weight") + ":Float:150"
        ]
        data = get_customer_data(filters)
    elif party_type == 'Supplier':
        columns = [
            _("Supplier Name") + "::150",
            _("Annual Billing Amount") + ":Currency:150",
            _("Outstanding Amount") + ":Currency:150",
            _("Total Quantity") + ":Float:150",
            _("Total Weight") + ":Float:150"
        ]
        data = get_supplier_data(filters)

    return columns, data

def get_customer_data(filters):
    conditions = "WHERE si.customer = %(party)s AND si.docstatus = 1" if filters.get('party') else "WHERE si.docstatus = 1"
    
    query = f"""
        SELECT
            si.customer_name AS `customer_name`,
            SUM(si.grand_total) AS `annual_billing_amount`,
            SUM(IFNULL(si.total_qty, 0)) AS `total_quantity`,
            SUM(IFNULL(si.custom_net_weight, 0)) AS `total_weight`
        FROM `tabSales Invoice` si
        JOIN `tabCustomer` c ON si.customer = c.name
        {conditions}
        GROUP BY c.customer_name
    """
    
    data = frappe.db.sql(query, {'party': filters.get('party')}, as_dict=True)
    for row in data:
        row['outstanding_amount'] = get_customer_outstanding(row['customer_name'])
    return data

def get_supplier_data(filters):
    conditions = "WHERE pi.supplier = %(party)s AND pi.docstatus = 1" if filters.get('party') else "WHERE pi.docstatus = 1"
    
    query = f"""
        SELECT
            s.supplier_name AS `supplier_name`,
            SUM(pi.grand_total) AS `annual_billing_amount`,
            SUM(IFNULL(pi.total_qty, 0)) AS `total_quantity`,
            SUM(IFNULL(pi.custom_net_weight, 0)) AS `total_weight`
        FROM `tabPurchase Invoice` pi
        JOIN `tabSupplier` s ON pi.supplier = s.name
        {conditions}
        GROUP BY s.supplier_name
    """
    
    data = frappe.db.sql(query, {'party': filters.get('party')}, as_dict=True)
    for row in data:
        row['outstanding_amount'] = get_supplier_outstanding(row['supplier_name'])
    return data

def get_customer_outstanding(customer, ignore_outstanding_sales_order=False, cost_center=None):
    companies = frappe.get_all('Company', fields=['name'])
    total_outstanding = 0

    for company in companies:
        company_name = company['name']
        cond = ""
        if cost_center:
            lft, rgt = frappe.get_cached_value("Cost Center", cost_center, ["lft", "rgt"])
            cond = f""" and cost_center in (select name from `tabCost Center` where
                lft >= {lft} and rgt <= {rgt})"""
        outstanding_based_on_gle = frappe.db.sql(
            f"""
            SELECT COALESCE(SUM(debit) - SUM(credit), 0) AS outstanding_amount
            FROM `tabGL Entry`
            WHERE party_type = 'Customer'
            AND is_cancelled = 0
            AND party = %s
            AND company = %s {cond}
            """,
            (customer, company_name),
        )

        outstanding_based_on_gle = flt(outstanding_based_on_gle[0][0])

        total_outstanding += outstanding_based_on_gle 

    return total_outstanding

def get_supplier_outstanding(supplier, cost_center=None):
    companies = frappe.get_all('Company', fields=['name'])
    total_outstanding = 0

    for company in companies:
        company_name = company['name']
        cond = ""
        if cost_center:
            lft, rgt = frappe.get_cached_value("Cost Center", cost_center, ["lft", "rgt"])
            cond = f""" and cost_center in (select name from `tabCost Center` where
                lft >= {lft} and rgt <= {rgt})"""

        outstanding_based_on_gle = frappe.db.sql(
            f"""
            SELECT COALESCE(SUM(credit) - SUM(debit), 0) AS outstanding_amount
            FROM `tabGL Entry`
            WHERE party_type = 'Supplier'
            AND is_cancelled = 0
            AND party = %s
            AND company = %s {cond}
            """,
            (supplier, company_name),
        )

        outstanding_based_on_gle = flt(outstanding_based_on_gle[0][0])
        total_outstanding += outstanding_based_on_gle 
    return total_outstanding
