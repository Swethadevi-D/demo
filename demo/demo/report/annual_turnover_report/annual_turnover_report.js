
frappe.query_reports["Annual Turnover report"] = {
    "filters": [
        {
            fieldname: "party_type",
            label: __("Party Type"),
            fieldtype: "Select",
            options: [
                { "value": "Customer", "label": __("Customer") },
                { "value": "Supplier", "label": __("Supplier") }
            ],
            on_change: function () {
                // Clear and refresh the party filter value when party_type changes
                frappe.query_report.set_filter_value("party", "");
                frappe.query_report.refresh();
            }
        },
        {
            fieldname: "party",
            label: __("Party"),
            fieldtype: "Link",
            options: function() {
                let party_type = frappe.query_report.get_filter_value("party_type");
                return party_type; // Set options dynamically based on party_type
            },
            get_query: function() {
                let party_type = frappe.query_report.get_filter_value("party_type");
                if (party_type) {
                    return {
                        doctype: party_type // Set the doctype for the link field based on party_type
                    };
                }
            }
        }
    ]
};
