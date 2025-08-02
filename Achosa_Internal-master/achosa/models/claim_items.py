from odoo import models, fields, api, _


class claim_items(models.Model):
    _name = 'claim.items'
    _order = 'claims_id,id'
    _description = "Claim items"

    # Claim this item belongs to
    claims_id = fields.Many2one("claims", string="Claim", ondelete="restrict", store="True")

    # Product repaired
    product_id = fields.Many2one("product.product", string="Item Repaired", ondelete="restrict", store="True")

    # Claim Amount Requested
    repair_amt = fields.Float("Cost")

    # Date Amount was requested
    repair_date = fields.Datetime("Date Repaired")

    # Claim Item Amount Approved
    approved_amt = fields.Float("Amount Approved")

    # Date amount was approved
    approved_date = fields.Datetime("Date Approved")

    # Claim Item Amount Requested
    requested_amt = fields.Float("Amount Requested")

    # Date Amount was requested
    requested_date = fields.Datetime("Date Requested")

    # Claim Item Amount paid
    paid_amt = fields.Float("Amount Paid")

    # Date paid
    paid_date = fields.Datetime("Date Paid")

    # status of claim
    status = fields.Selection([('Repaired', 'Repaired'), ('Replaced', 'Replaced')]
                              , string="Status")

    # Claim Subscription Line Item
    subscription_line = fields.Many2one("sale.subscription.line", related="claims_id.product")

    # display name
    def name_get(self):
        res = []

        for rec in self:
            name = rec.claims_id.name + " - " + rec.product_id.name
            res.append((rec.id, name))
        return res

    @api.model
    def create(self, vals):
        r = super(claim_items, self).create(vals)
        if r.claims_id:
            r.claims_id._compute_item_name()
        return r

    def write(self, vals):
        res = super(claim_items, self).write(vals)
        for r in self:
            if r.claims_id:
                r.claims_id._compute_item_name()
        return res
