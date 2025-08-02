# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if args and isinstance(args, list):
            args.append(('sale_team_id', '=', self.env.ref('sales_team.team_sales_department').id))
        else:
            args = [('sale_team_id', '=', self.env.ref('sales_team.team_sales_department').id)]
        return super(ResUsers, self)._name_search(name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)