def sales_invoice_naming(self, events):
    
    if (self.is_return == 1):
        sales_return_naming(self , events)
    else:
        if self.company == 'SMT PAVER AND BLOCKS':
            if self.non_gst:  
                self.name = make_autoname('AGG-SI-.##', self)
            else:
                self.name = make_autoname('SMT-SI-.YY.-.##', self)

def sales_return_naming(self, events):
   
    if self.company == 'SMT PAVER AND BLOCKS':
        self.name = make_autoname('SMT-RTRN-.YY.-.##', self)
    if self.company == 'SMT FLYASH BRICKS':
        self.name = make_autoname('SFB-RTRN-.YY.-.##', self)
    if self.company == 'TIRUPUR BRICKS AND BLOCKS':
        self.name = make_autoname('TBAB-RTRN-.YY.-.##', self)
        
def make_autoname(key="", doctype="", doc="", *, ignore_validate=False):
	"""
	     Creates an autoname from the given key:

	     **Autoname rules:**

	              * The key is separated by '.'
	              * '####' represents a series. The string before this part becomes the prefix:
	                     Example: ABC.#### creates a series ABC0001, ABC0002 etc
	              * 'MM' represents the current month
	              * 'YY' and 'YYYY' represent the current year


	*Example:*

	              * DE./.YY./.MM./.##### will create a series like
	                DE/09/01/00001 where 09 is the year, 01 is the month and 00001 is the series
	"""
	if key == "hash":
		return frappe.generate_hash(length=10)

	series = NamingSeries(key)
	return series.generate_next_name(doc, ignore_validate=ignore_validate)