# -*- coding: utf-8 -*-
# Copyright (C) Reliution Consulting Services.

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class RcsFieldMapping(models.Model):
    _name = "rcs.address.field.mapping"
    _rec_name = 'model_id'

    model_id = fields.Many2one("ir.model" )
    line_ids = fields.One2many("rcs.address.field.mapping.line", "mapping_id", string="Field Mappings")
    widget_field_id = fields.Many2one(
        "ir.model.fields",
        string="Widget Field",
        domain="[('model_id', '=', model_id)]",
        copy=False,
    )

    _sql_constraints = [
        ('widget_field_id_uniq', 'unique (widget_field_id)', 'Widget Field already exist.'),
    ]
    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.widget_field_id=False
        self.line_ids = False

    @api.constrains("line_ids")
    def _check_unique_labels(self):
        for record in self:
            labels = record.line_ids.mapped("label")
            if len(labels) != len(set(labels)):
                raise ValidationError("You cannot assign the same label multiple times.")

class RcsFieldMappingLine(models.Model):
    _name = "rcs.address.field.mapping.line"

    mapping_id = fields.Many2one("rcs.address.field.mapping" , ondelete="cascade")
    label = fields.Selection([
        ('STREET', 'Street'),
        ('STREET2', 'Street 2'),
        ('CITY', 'City'),
        ('STATE', 'State'),
        ('ZIP', 'Zip Code'),
        ('COUNTRY', 'Country'),
    ], string="Label")

    model_id = fields.Many2one(related="mapping_id.model_id", store=False)
    fields_type=fields.Char()
    field_id = fields.Many2one(
        "ir.model.fields",
        string="Mapped Field",
    )

    @api.onchange('label', 'model_id')
    def _onchange_label(self):
        self.field_id=False
        if self.label and self.model_id:

            base_domain = [('model_id', '=', self.model_id.id)]
            char_like = ['char', 'text', 'html']

            if self.label in ['STREET', 'STREET2', 'CITY']:
                domain = base_domain + [('ttype', 'in', char_like)]
                self.fields_type = domain
            elif self.label == 'ZIP':
                domain = base_domain + [('ttype', 'in', char_like + ['integer'])]
                self.fields_type = domain
            elif self.label == 'STATE':
                domain = base_domain + [('ttype', '=', 'many2one'), ('relation', '=', 'res.country.state')]
                self.fields_type = domain
            elif self.label == 'COUNTRY':
                domain = base_domain + [('ttype', '=', 'many2one'), ('relation', '=', 'res.country')]
                self.fields_type = domain
            else:
                domain = base_domain
                self.fields_type=domain
        else:
            self.fields_type=[('model_id', '=', self.model_id.id)]

    _sql_constraints = [
        ('field_id_not_null', 'CHECK(field_id IS NOT NULL)', 'Mapping Field cannot be empty'),
        ('label_not_null', 'CHECK(label IS NOT NULL)', 'Label cannot be empty'),
        ('field_id_uniq', 'unique (field_id)', 'Field already exist.'),
    ]

