import frappe 

def createTransportJE(doc, events):
    if (doc.is_new == 0):
        return
    account = ""
    exp_account = ""
    if doc.custom_vehicle:
      
        if doc.company == 't':
            account = "Debtors - t"
            exp_account = "Transport Charges - t"    
        journal_entry = frappe.new_doc("Journal Entry")
        journal_entry.company = doc.company
        journal_entry.posting_date = doc.posting_date
        total_amount = float(doc.custom_rent_per_km) * float(doc.custom_total_km)
        doc.custom_total_amount=total_amount
        if account:
            journal_entry.append("accounts", {
                "account": account, 
                "party_type": "Customer",
                "party": doc.customer,
                "credit_in_account_currency": total_amount
            })

            journal_entry.append("accounts", {
                "account": exp_account, 
                "debit_in_account_currency": total_amount
            })

            journal_entry.save()

            frappe.db.set_value("Sales Invoice", doc.name, 'custom_journal_entry', journal_entry.name)
            doc.reload()
        else:
            frappe.msgprint("Account not found for company: {}".format(doc.company))


