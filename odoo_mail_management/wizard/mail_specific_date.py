from datetime import datetime

from markupsafe import Markup
from odoo import api, fields, models, _
from odoo.tools.mail import is_html_empty

class FetchMailsBetweenDates(models.TransientModel):
    _name = "fetch.mails.between.dates"
    _description = "Fetch Mails Between Dates"

    from_date=fields.Date(default=datetime.now())
    to_date=fields.Date(default=datetime.now())
    fetchmail_server_id = fields.Many2one(
        'fetchmail.server', string="Mail Server", required=True
    )

    def fetch_mails_between_dates(self):
        self.fetchmail_server_id.with_context(is_wizard=True,from_date=self.from_date,to_date=self.to_date).fetch_mail()
