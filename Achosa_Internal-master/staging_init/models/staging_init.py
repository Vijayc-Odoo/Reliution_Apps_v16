from odoo import models
from odoo.exceptions import UserError
import logging
import os
import time
_logger = logging.getLogger("###STAGING INIT###")


class PaymentAcquirerAuthorize(models.Model):
    _inherit = 'payment.acquirer'
    
    def _check_staging(self):
        time.sleep(30)
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        if "dev.odoo.com" in base_url and os.environ.get('ODOO_STAGE') == "staging":
            _logger.info("PASSED CHECK")

            return True
        else:
            _logger.info("FAILED CHECK")
            raise UserError("This Instance Has Failed the Staging Check! Aborting...")

    
    
    def staging_update_tokens(self):
        company_id = self.env.company
        authorize = self.env['payment.acquirer'].search([("provider","=","authorize")])
        for auth in authorize:
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            if "dev.odoo.com" in base_url and auth.state == "test" and auth.authorize_login == "dummy" and os.environ.get('ODOO_STAGE') == "staging":
                authorize_login = company_id.authorize_login_test
                authorize_transaction_key = company_id.authorize_transaction_key_test
                authorize_signature_key = company_id.authorize_signature_key_test
                _logger.info(f"Found Credentials from Company: [{company_id.name}, {authorize_login}, {authorize_transaction_key}, {authorize_signature_key}] STAGING INIT RUNNING>>>>>>UNINSTALL TO CANCEL>>>>>>>") 
                time.sleep(30)
                # auth.write({"authorize_login":authorize_login, "authorize_transaction_key":authorize_transaction_key, "authorize_signature_key":authorize_signature_key})
                # auth.action_update_merchant_details()
                # _logger.info("Authorize transaction failed, updating test credentials for Authorize.  Please try the transaction again in a few minutes.")
            else:
                _logger.info("PAYMENT ACQUIRER INITIALIZATION FAILED")
                
    
class Users(models.Model):
    _inherit = "res.users"

    def _init_users(self, vals):
        active_search = self.search([("login", "=", vals["login"]), ("active", "=", True)])
        archived_search = self.search([("login", "=", vals["login"]), ("active", "=", False)])
        if len(active_search) == 0 and len(archived_search) == 0:
            _logger.info(f"User {vals['login']} not found, creating user...")
            self.create(vals) if vals else {}
        else:
            _logger.info(f"User {vals['login']} found!, unarchiving if needed...")
            for rec in archived_search:
                rec.active = True
        return