# -*- coding: utf-8 -*-
# Copyright (C) Reliution Consulting Services.

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class RcsFieldMapping(models.Model):
    _name = "rcs.address.field.mapping"
    _rec_name = 'model_id'

    model_id = fields.Many2one("ir.model")
    line_ids = fields.One2many("rcs.address.field.mapping.line", "mapping_id", string="Field Mappings", ondelete='cascade')
    widget_field_id = fields.Many2one(
        "ir.model.fields",
        string="Widget Field",
        domain="[('model_id', '=', model_id)]"
    )

    _sql_constraints = [
        ('widget_field_id_uniq', 'unique (widget_field_id)', 'Widget Field already exist.'),
    ]
    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.line_ids.field_id = False

    @api.constrains("line_ids")
    def _check_unique_labels(self):
        for record in self:
            labels = record.line_ids.mapped("label")
            if len(labels) != len(set(labels)):
                raise ValidationError("You cannot assign the same label multiple times.")


class RcsFieldMappingLine(models.Model):
    _name = "rcs.address.field.mapping.line"

    mapping_id = fields.Many2one("rcs.address.field.mapping")
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
        # domain=lambda self: self.fields_type

    )

    @api.onchange('label', 'model_id')
    def _onchange_label(self):
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
            self.fields_type=[]


    def _get_field_domain(self):
        a=self.fields_type
        return a or []
    # @api.constrains('field_id')
    # def _check_global_unique_field_id(self):
    #     for record in self:
    #         existing = self.search([
    #             ('field_id', '=', record.field_id.id),
    #             ('id', '!=', record.id)
    #         ])
    #         if existing:
    #             raise ValidationError(f"{record.field_id.name}({record.model_id.name}) field already exist")

    _sql_constraints = [
        ('field_id_not_null', 'CHECK(field_id IS NOT NULL)', 'Mapping Field cannot be empty'),
        ('label_not_null', 'CHECK(label IS NOT NULL)', 'Label cannot be empty'),
        ('field_id_uniq', 'unique (field_id)', 'Field already exist.'),
    ]

