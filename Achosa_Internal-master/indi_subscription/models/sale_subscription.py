# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

_LOGGER = logging.getLogger("##### Indimedi Sale Subscription #####")


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    close_reason_id = fields.Many2one("sale.subscription.close.reason", string="Close/Cancel Reason", copy=False,
                                      tracking=True)
    in_cancelled = fields.Boolean(related='stage_id.in_cancelled')

    def prepare_achosa_subscription_vals(self, stage, date=fields.Date.today(), to_renew=False):
        return {'stage_id': stage.id, 'to_renew': to_renew, 'date': date}

    def set_close(self):
        sale_subscription_stage_obj = self.env['sale.subscription.stage']
        for subscription_id in self:
            stage_id = sale_subscription_stage_obj.search(
                [('category', '!=', 'progress'), ('sequence', '>', subscription_id.stage_id.sequence)], limit=1)
            if not stage_id:
                stage_id = sale_subscription_stage_obj.search([('category', '!=', 'progress')], limit=1)
            subscription_id.write(subscription_id.prepare_achosa_subscription_vals(stage_id))
            _LOGGER.info(f"Subscription: [{subscription_id.name}] closed]")
        return True

    def set_cancel(self):
        sale_subscription_stage_obj = self.env['sale.subscription.stage']
        for subscription_id in self:
            end_date = subscription_id._get_subscription_end_date('cancel')
            if end_date and not self.date and end_date > fields.Date.today():
                end_date = end_date - timedelta(days=1)

            stage = sale_subscription_stage_obj.search([('in_cancelled', '=', True)], limit=1)
            if stage:
                _LOGGER.info(f"End Date: [{end_date}]")
                subscription_id.write(subscription_id.prepare_achosa_subscription_vals(stage, date=end_date))
                _LOGGER.info(f"Subscription: [{subscription_id.name}] cancelled]")
        return True

    @api.model
    def cron_account_analytic_account(self):
        today = fields.Date.today()
        next_month = fields.Date.to_string(fields.Date.from_string(today) + relativedelta(months=1))

        # set to pending if date is in less than a month
        domain_pending = [('date', '<', next_month), ('stage_category', '=', 'progress')]
        subscriptions_pending = self.search(domain_pending)
        subscriptions_pending.set_to_renew()

        # set to close if date is passed
        domain_close = [('date', '<', today), '|', '|', ('stage_category', '=', 'progress'), ('to_renew', '=', True),
                        ('in_cancelled', '=', True)]
        subscriptions_close = self.search(domain_close)
        subscriptions_close.set_close()

        return dict(pending=subscriptions_pending.ids, closed=subscriptions_close.ids)
