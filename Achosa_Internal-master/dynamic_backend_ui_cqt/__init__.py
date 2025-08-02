# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID
from . import models

def _post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['dynamic.colors'].update_scss_dynamic_attachment()
