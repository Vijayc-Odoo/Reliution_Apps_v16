import logging
import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

_logger = logging.getLogger("##### Achosa #####")

emails_split = re.compile(r"[;,\n\r]+")

class SurveyInvite(models.TransientModel):
    _inherit = 'survey.invite'
    
    def _prepare_answers(self, partners, emails):
        answers = self.env['survey.user_input']
        existing_answers = self.env['survey.user_input'].search([
            '&', ('survey_id', '=', self.survey_id.id),
            '|',
            ('partner_id', 'in', partners.ids),
            ('email', 'in', emails)
        ])
        partners_done = self.env['res.partner']
        emails_done = []

        for new_partner in partners - partners_done:
            answers |= self.survey_id._create_answer(partner=new_partner, check_attempts=False, **self._get_answers_values())
        for new_email in [email for email in emails if email not in emails_done]:
            answers |= self.survey_id._create_answer(email=new_email, check_attempts=False, **self._get_answers_values())

        return answers
    
class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'
    
    survey_score_average = fields.Float('Average Score', compute="_compute_average_score")
    
    def _compute_average_score(self):
        for user_input in self:
            count = 0
            sum_values = 0
            for value in user_input.user_input_line_ids.mapped('suggested_answer_id'):
                if value.value in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']:
                    sum_values += float(value.value)
                    count += 1
            if count == 0:
                self.survey_score_average = 0
            else:
                self.survey_score_average = sum_values / count

