from odoo import models, fields, api, _


class vendor_zip_codes(models.Model):
    _name = 'vendor.zip.codes'
    _order = 'vendor,zip_code'
    _description = "cross walk of vendors to use for repairs and the zip codes they work in"

    # Claim this item belongs to
    vendor = fields.Many2one("res.partner", string="Vendors", ondelete="restrict",
                             store="True")

    # Product repaired
    zip_code = fields.Char("Zip Code",
                           store="True")
