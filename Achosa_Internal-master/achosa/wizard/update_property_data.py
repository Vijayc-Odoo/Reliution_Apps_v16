# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
import logging, re
import requests

_logger = logging.getLogger("##### Achosa #####")

class UpdatePropertyData(models.TransientModel):
    """
        Merge opportunities together.
        If we're talking about opportunities, it's just because it makes more sense
        to merge opps than leads, because the leads are more ephemeral objects.
        But since opportunities are leads, it's also possible to merge leads
        together (resulting in a new lead), or leads and opps together (resulting
        in a new opp).
    """

    _name = 'update.property.data'
    _description = 'Update Property Data'

    @api.model
    def default_get(self, fields):
        """ Use active_ids from the context to fetch the leads/opps to merge.
            In order to get merged, these leads/opps can't be in 'Dead' or 'Closed'
        """
        record_ids = self._context.get('active_ids') or []
        result = super(UpdatePropertyData, self).default_get(fields)
        result['home_warranty_ids'] = [(6, 0, record_ids)]

        return result

    home_warranty_ids = fields.Many2many('home.warranty', 'update_property_data_rel', 'update_id', 'home_warranty_id',
                                         string='Home Warranties')

    def action_update(self):
        self.ensure_one()
        _logger.log(logging.INFO, str(self.home_warranty_ids))

        for home_warranty in self.home_warranty_ids:
            self.get_Zestiment(home_warranty)

        return True

    @api.depends('home_warranty')
    def get_Zestiment(self, home_warranty):
        url = ''
        company_id = home_warranty.company_id or self.env.company
        _logger.info(f"Method: get_Zestiment, Company: [{company_id.name}]")
        try:
            token = company_id.estated_token or \
                    'h7FbxJPHSiFHJ4yRqcVO34raGj5Fd8'
            url = company_id.estated_url or \
                  'https://sandbox.estated.com/v4/property?token={}&combined_address={},+{},+{}+{}'
            url = url.format(token,home_warranty.property_street, home_warranty.property_city,
                             home_warranty.property_state_code, home_warranty.property_zip).replace(' ', '+')
            _logger.info(url)
            response = requests.get(url)
            home_warranty.estated_json = str(response.json())
            home_warranty.estated_date = datetime.today()
            if('warnings' in response.json() and response.json()['warnings']):
                w = response.json()['warnings'][0]
                home_warranty.estated_warning = str('{}: {} - {}'.format(w['code'],w['title'],w['description']))
                _logger.warning(response.json()['warnings'])
            if('data' in response.json() and response.json()['data']):
                data = response.json()['data']
                _logger.info(data)
                home_warranty.s_year_built = str(data['structure']['year_built'])
                home_warranty.total_area_sq_ft = str(data['structure']['total_area_sq_ft'])
                home_warranty.standardized_land_use_type = str(data['parcel']['standardized_land_use_type'])
                home_warranty.value = str(data['valuation']['value'])
                home_warranty.value_low = str(data['valuation']['low'])
                home_warranty.value_high = str(data['valuation']['high'])
        except Exception as error:
            _logger.error("Error loading Estated Data for "+self.home_warranty.name + "\n" +
                          url)
            _logger.exception(error)
