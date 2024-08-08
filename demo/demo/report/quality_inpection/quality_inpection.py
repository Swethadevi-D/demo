
# import frappe
# from frappe import _

# def execute(filters=None):
#     columns = get_columns()
#     data = get_data(filters)
#     return columns, data

# def get_columns():
#     columns = [
#         {
#             "label": _("Quality Inspection ID"),
#             "fieldname": "quality_inspection_id",
#             "fieldtype": "Link",
#             "options": "Quality Inspection",
#             "width": 200
#         },
#         {
#             "label": _("Item Name"),
#             "fieldname": "item_name",
#             "fieldtype": "Link",
#             "options": "Item",
#             "width": 200
#         },
#         {
#             "label": _("Test Value"),
#             "fieldname": "test_value",
#             "fieldtype": "Float",
#             "width": 100
#         },
#         {
#             "label": _("Reading"),
#             "fieldname": "reading",
#             "fieldtype": "Float",
#             "width": 100
#         },
#         {
#             "label": _("Strength"),
#             "fieldname": "strength",
#             "fieldtype": "Float",
#             "width": 100
#         }
#     ]
#     return columns

# def get_data(filters):
#     # Fetch quality inspections
#     inspections = frappe.get_all('Quality Inspection', fields=['name', 'item_code'])
    
#     data = []
#     for inspection in inspections:
#         quality_inspection_id = inspection['name']
#         item_name = frappe.db.get_value('Item', inspection.item_code, 'item_name')
#         test_value_str = frappe.db.get_value('Item', inspection.item_code, 'custom_value')  # assuming test_value is a custom field in Item
        
#         # Convert test_value to float, handle None case
#         test_value = float(test_value_str) if test_value_str else None
        
#         # Fetch readings
#         readings = frappe.get_all('Quality Inspection Reading', filters={'parent': inspection.name}, fields=['numeric', 'reading_1', 'reading_2', 'reading_3', 'reading_4', 'reading_5', 'reading_6', 'reading_7', 'reading_8', 'reading_9', 'reading_10'])
        
#         for reading in readings:
#             if reading['numeric']:  # Check if numeric checkbox is checked
#                 for idx in range(1, 11):
#                     reading_field = 'reading_{0}'.format(idx)
#                     strength_field = 'strength_{0}'.format(idx)
                    
#                     # Convert reading_value to float, handle None case
#                     reading_value_str = reading.get(reading_field)
#                     reading_value = float(reading_value_str) if reading_value_str else None
                    
#                     if reading_value:  # Only add row if reading_value is not None
#                         if test_value:
#                             strength = reading_value * 1000 / test_value
#                         else:
#                             strength = None
                        
#                         row = {
#                             "quality_inspection_id": quality_inspection_id,
#                             "item_name": item_name,
#                             "test_value": test_value,
#                             "reading": reading_value,
#                             "strength": strength
#                         }
                        
#                         data.append(row)
#             else:
#                 # Add a row with None values if numeric is not checked
#                 # This part is optional based on your requirement
#                 row = {
#                     "quality_inspection_id": quality_inspection_id,
#                     "item_name": item_name,
#                     "test_value": test_value,
#                     "reading": None,
#                     "strength": None
#                 }
#                 data.append(row)
    
#     return data
import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    columns = [
        {
            "label": _("Quality Inspection ID"),
            "fieldname": "quality_inspection_id",
            "fieldtype": "Link",
            "options": "Quality Inspection",
            "width": 200
        },
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Link",
            "options": "Item",
            "width": 200
        },
        {
            "label": _("Test Value"),
            "fieldname": "test_value",
            "fieldtype": "Float",
            "width": 100
        },
        {
            "label": _("Reading"),
            "fieldname": "reading",
            "fieldtype": "Float",
            "width": 100
        },
        {
            "label": _("Strength"),
            "fieldname": "strength",
            "fieldtype": "Float",
            "width": 100
        }
    ]
    return columns

def get_data(filters):
    conditions = []
    if filters.get('start_date'):
        conditions.append(['report_date', '>=', filters.get('start_date')])
    if filters.get('end_date'):
        conditions.append(['report_date', '<=', filters.get('end_date')])
    if filters.get('item_code'):
        conditions.append(['item_code', '=', filters.get('item_code')])
    
    inspections = frappe.get_all('Quality Inspection', filters=conditions, fields=['name', 'item_code'])
    
    data = []
    for inspection in inspections:
        quality_inspection_id = inspection['name']
        item_name = frappe.db.get_value('Item', inspection.item_code, 'item_name')
        test_value_str = frappe.db.get_value('Item', inspection.item_code, 'custom_value')
        
        test_value = float(test_value_str) if test_value_str else None
        
        readings = frappe.get_all('Quality Inspection Reading', filters={'parent': inspection.name}, fields=['numeric', 'reading_1', 'reading_2', 'reading_3', 'reading_4', 'reading_5', 'reading_6', 'reading_7', 'reading_8', 'reading_9', 'reading_10'])
        
        for reading in readings:
            if reading['numeric']:
                for idx in range(1, 11):
                    reading_field = 'reading_{0}'.format(idx)
                    strength_field = 'strength_{0}'.format(idx)
                    
                    reading_value_str = reading.get(reading_field)
                    reading_value = float(reading_value_str) if reading_value_str else None
                    
                    if reading_value:
                        if test_value:
                            strength = reading_value * 1000 / test_value
                        else:
                            strength = None
                        
                        row = {
                            "quality_inspection_id": quality_inspection_id,
                            "item_name": item_name,
                            "test_value": test_value,
                            "reading": reading_value,
                            "strength": strength
                        }
                        
                        data.append(row)
            else:
                row = {
                    "quality_inspection_id": quality_inspection_id,
                    "item_name": item_name,
                    "test_value": test_value,
                    "reading": None,
                    "strength": None
                }
                data.append(row)
    
    return data
