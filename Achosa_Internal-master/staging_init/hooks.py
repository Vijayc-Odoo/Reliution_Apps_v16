from odoo import models, fields, api, SUPERUSER_ID
from .models import staging_init
import logging
import os

_logger = logging.getLogger("###STAGING_INIT###")


def post_init_hook(cr, registry):
    _logger.info("POST INIT HOOK RUNNING.....")
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    pay = env['payment.acquirer']
    users = env['res.users']
    if pay._check_staging():
        pay._update_authorize_dev_tokens()
        charles = {
            'name': "Charles Robinson",
            'login': "charles.robinson@restyn.com",
            'password': "sexybeast",
            'sel_groups_1_10_11': 1
        }
        nathan = {
            'name': "Nathan Lakomy",
            'login': "nlakomy@cripca.com",
            'password': "audit4Achosa",
            'sel_groups_1_10_11': 1
        }

        users._init_users(charles)
        users._init_users(nathan)
    else:
        _logger.info("staging check failed, halting staging_init...")
