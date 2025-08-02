import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger("##### Achosa #####")


class CloseReason(models.Model):
    _inherit = 'sale.subscription.close.reason'

    cancellation_reason = fields.Boolean('Cancellation Reason')

    @api.constrains('cancellation_reason')
    def _check_cancellation_reason(self):
        if self.search_count([('cancellation_reason', '=', True)]) > 1:
            raise ValidationError(_('You cannot have multiple reasons as cancellation!'))


class SubscriptionAnniversary(models.Model):
    _name = "sale.subscription"
    _inherit = ['sale.subscription', 'portal.mixin']

    is_cancellation_request = fields.Boolean('Cancellation Request Generated?')
    anniversary_date = fields.Date(string="Anniversary Date", help="Subscription Anniversary Date")
    next_anniversary_date = fields.Date(string="Next Anniversary Date", help="Subscription Anniversary Date")
    anniversary_number = fields.Integer(string="Anniversary Number", default=0, help="Subscription Anniversary Number")

    def auto_cancel_subscriptions(self):
        cancel_stage_rec = self.env['sale.subscription.stage'].search([('in_cancelled', '=', True)])
        progress_stages = self.env['sale.subscription.stage'].search([('category', '=', 'progress')])
        subscriptions = self.env['sale.subscription'].search([('order_type', '=', 'Owner'),
                                                              ('date', '=', date.today()),
                                                              ('stage_id', 'in', progress_stages.ids)])
        template = self.env.ref('achosa.subscriber_cancellation_mail')
        for subscription in subscriptions:
            subscription.stage_id = cancel_stage_rec and cancel_stage_rec.id
            #             template.send_mail(subscription.id, force_send=True)
            subscription.message_post_with_template(template.id, composition_mode='comment')

    def _compute_access_url(self):
        super(SubscriptionAnniversary, self)._compute_access_url()
        for sub in self:
            sub.access_url = '/my/subscription/cancel/%s' % sub.id

    def _get_buyer_seller_subscription(self):
        return self.search([('partner_id', '=', self.partner_id.id), ('order_type', 'in', ['Buyer', 'Seller']),
                            ('home_warranty', '=', self.home_warranty.id)], limit=1)

    def _prepare_anniversary_subscription_domain(self, from_date, to_date, stage_id):
        domain = [
            ('order_type', '=', 'Owner'),
            ('stage_id', '!=', stage_id.id),
            ('home_warranty', '!=', False),
            ('next_anniversary_date', '!=', False),
            ('next_anniversary_date', '>=', from_date),
            ('next_anniversary_date', '<=', to_date),
            '|',
            ('date', '=', False),
            '&',
            ('date', '!=', False),
            ('date', '>=', date.today())
        ]
        return domain

    def _get_anniversary_subscriptions(self, from_date, to_date, stage_id, sorting_key=''):
        domain = self._prepare_anniversary_subscription_domain(from_date, to_date, stage_id)
        if sorting_key:
            subscription_ids = self.search(domain).sorted(lambda x: x[sorting_key])
        else:
            subscription_ids = self.search(domain)

        _logger.info(f"Method: [_get_anniversary_subscriptions], Domain: [{domain}], "
                     f"Subscriptions: [{subscription_ids.ids}]")
        return subscription_ids

    def get_filtered_anniversary_subscription(self, target_date, anniversary_months, security_date):
        subscription_ids = self.env['sale.subscription']
        for subscription_id in self:
            filtered_date = subscription_id.date_start.replace(
                year=target_date.year) + relativedelta(months=-anniversary_months)
            if filtered_date >= security_date and filtered_date <= target_date:
                subscription_ids += subscription_id
        return subscription_ids

    def _get_anniversary_target_date(self, target_date, anniversary_month, use_anniversary_month=True):
        if target_date and isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%m/%d/%Y").date()
        if not target_date:
            target_date = date.today()
        if use_anniversary_month:
            target_date += relativedelta(months=anniversary_month)
        return target_date

    def _get_anniversary_dates(self, security_days, target_date, anniversary_month, use_anniversary_month=True):
        to_date = self._get_anniversary_target_date(target_date, anniversary_month,
                                                    use_anniversary_month=use_anniversary_month)
        from_date = to_date - timedelta(days=security_days)
        return from_date, to_date

    # def cron_anniversary_email(self, security_days=3, target_date=date.today(), anniversary_month=1):
    #     from_date, to_date = self._get_anniversary_dates(security_days=security_days, target_date=target_date,
    #                                                      anniversary_month=anniversary_month)
    #     cron_start_date, cron_end_date = self._get_anniversary_dates(security_days=security_days,
    #                                                                  target_date=target_date,
    #                                                                  anniversary_month=anniversary_month,
    #                                                                  use_anniversary_month=False)
    #     template_id = self.env.ref('achosa.subscriber_anniversary_mail')
    #     stage_id = self.env.ref('sale_subscription.sale_subscription_stage_closed')
    #     subscription_ids = self._get_anniversary_subscriptions(from_date=from_date, to_date=to_date,
    #                                                            stage_id=stage_id, sorting_key='date_start')
    #     message = f"Method: [cron_anniversary_email], Total found Subscriptions: {subscription_ids.ids}"
    #     _logger.info(message)
    #     for subscription_id in subscription_ids:
    #         subscription_end_date = subscription_id.date.strftime("%Y/%m/%d") if subscription_id.date else ''
    #         _logger.info(f"Method: [cron_anniversary_email], Subscription: [{subscription_id.name}], "
    #                      f"Subscription Date Start: [{subscription_id.date_start.strftime('%m/%d/%Y')}], "
    #                      f"Subscription End Date: [{subscription_end_date}]")
    #         anniversary_date, anniversary_number = subscription_id. \
    #             get_subscription_anniversary_date_and_number(start_date=subscription_id.date_start, end_date=to_date)
    #         if subscription_id.check_mismatch_details_for_anniversary_mail(anniversary_number=anniversary_number,
    #                                                                        anniversary_date=anniversary_date,
    #                                                                        template_id=template_id,
    #                                                                        from_date=cron_start_date,
    #                                                                        to_date=cron_end_date):
    #             continue
    #         next_anniversary_date = anniversary_date + relativedelta(years=1)
    #         values = {'anniversary_date': anniversary_date, 'anniversary_number': anniversary_number,
    #                   'next_anniversary_date': next_anniversary_date}
    #         _logger.info(f"Subscription: [{subscription_id.name}], Anniversary Mail Details: [{values}]")
    #         subscription_id.write(values)
    #         subscription_id.message_post_with_template(template_id.id, composition_mode='comment')
    #
    #         # send_mail(record.id, force_send=True)
    #     self.env['ir.logging'].create_ir_logging_record(
    #         function_name="[AO-880] | Anniversary Email - Investigate Anniversary Number",
    #         message=message, path='achosa/models/achosa_anniversary_email.py')
    #     return True

    def check_mismatch_details_for_anniversary_mail(self, anniversary_number, anniversary_date, template_id, from_date,
                                                    to_date):
        mismatch_detail = False
        mail_mail_obj = self.env['mail.message']
        mail_ids = mail_mail_obj.search_achosa_existing_mail(model_name=self._name, resource_id=self.id,
                                                             template_id=template_id, from_date=from_date,
                                                             to_date=to_date, search_mail_on_specific_date=True)
        if mail_ids:
            _logger.info(f"Method: [cron_anniversary_email], "
                         f"Skip to send the mail because it's  already exists, Mail: [{mail_ids.ids}]")
            mismatch_detail = True
        buyer_subscription_id = self._get_buyer_seller_subscription()
        if buyer_subscription_id and anniversary_number == 1:
            _logger.info(f"Method: [cron_anniversary_email], "
                         f"Skip to send the Subscription Anniversary Mail because the Owner subscription "
                         f"is recently converted from Buyer Subscription, "
                         f"Subscription: [{self.name}], Anniversary Date: [{anniversary_date}], "
                         f"Anniversary Number: [{anniversary_number}]")
            mismatch_detail = True

        return mismatch_detail

    def get_subscription_anniversary_date_and_number(self, start_date, end_date):
        anniversary_number = self._get_subscription_year(start_date=start_date, end_date=end_date)
        anniversary_date = self._get_anniversary_date(subscription_start_date=start_date,
                                                      years=anniversary_number - 1 if anniversary_number else 0)
        return anniversary_date, anniversary_number

    def _get_anniversary_date(self, subscription_start_date, years=0):
        return subscription_start_date + relativedelta(years=years)

    def _get_subscription_year(self, end_date, start_date):
        return relativedelta(end_date, start_date).years

    def _convert_anniversary_number_into_human_redable(self, number):
        anniversary_number = lambda n: "%d%s" % (n, {1: "st", 2: "nd", 3: "rd"}.get(n if n < 20 else n % 10, "th"))
        return anniversary_number(number)

    # def get_anniversary_details(self):
    #     self.ensure_one()
    #     anniversary_number = self._convert_anniversary_number_into_human_redable(number=self.anniversary_number)
    #     return {'anniversary_date': self.anniversary_date.strftime('%B %d, %Y'),
    #             'anniversary_number': anniversary_number}

    def cron_anniversary_email(self):
        subscriber = self.env['sale.subscription'].search([('order_type', '=', 'Owner')])
        today = date.today()
        owner_subscriber = subscriber.filtered(
            lambda l: ((l.date == False) or (l.date != False and l.date >= date.today()))
                      and l.stage_id != self.env.ref('sale_subscription.sale_subscription_stage_closed')
                      and (l.date_start.replace(year=today.year) + relativedelta(months=-1)) == today)
        message = 'Anniversary mail has been sent successfully for Subscriptions :'
        for record in owner_subscriber:
            record.get_anniversary_details()
            template = self.env.ref('achosa.subscriber_anniversary_mail')
            # buyer_subscription_id = record._get_buyer_seller_subscription()
            buyer_subscription_id = record.order_type in ['Buyer', 'Seller']
            # if it's a buyer (or seller) subscription, wait until the 2nd year, otherwise start at the first for owner subscriptions
            if (buyer_subscription_id and record.anniversary_number >= 2) or (
                    not buyer_subscription_id and record.anniversary_number >= 1):
                message += f"\n[{record.id}: {record.name}, anniversary number: {record.anniversary_number}]"

                record.message_post_with_template(template.id, composition_mode='comment')
        self.env['ir.logging'].create_ir_logging_record(
            function_name="Subscription Anniversary Email",
            message=message, path='achosa/models/achosa_anniversary_email.py')

    #             send_mail(record.id, force_send=True)

    def get_anniversary_details(self):
        self.ensure_one()
        today = date.today()
        subscriber_start_date = fields.Date.from_string(self.date_start)
        # Use a date 6 months in the future because it's more than the notice we're giving customers of the coming anniversary
        today_plus6mo = today + timedelta(days=180)
        delta = relativedelta(today_plus6mo, subscriber_start_date).years
        anniversary_date = subscriber_start_date + timedelta(days=delta * 365)
        same_buyer = self.env['sale.subscription'].search(
            [('partner_id', '=', self.partner_id.id), ('order_type', '=', 'Buyer'),
             ('home_warranty', '=', self.home_warranty.id)])
        buyer_term = same_buyer.filtered(
            lambda l: l.home_warranty and l.home_warranty.covered_buyer_term and isinstance(
                l.home_warranty.covered_buyer_term, str) and l.home_warranty.covered_buyer_term.isdigit())
        terms = buyer_term.mapped('home_warranty.covered_buyer_term')
        anniversary_number = int((sum([int(term) for term in terms])) / 12) + delta
        suf = lambda n: "%d%s" % (n, {1: "st", 2: "nd", 3: "rd"}.get(n if n < 20 else n % 10, "th"))
        self.anniversary_number = anniversary_number
        anniversary_number = suf(anniversary_number)
        self.anniversary_date = anniversary_date
        return {'anniversary_date': anniversary_date.strftime('%B %d, %Y'),
                'anniversary_number': anniversary_number}
