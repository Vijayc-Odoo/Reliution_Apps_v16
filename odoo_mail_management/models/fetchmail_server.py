import logging
from imaplib import IMAP4
import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
MAX_POP_MESSAGES = 50
MAIL_TIMEOUT = 60

class FetchmailServer(models.Model):
    """Incoming POP/IMAP mail server account"""

    _inherit = 'fetchmail.server'

    def fetch_mail(self, raise_exception=True):
        """ WARNING: meant for cron usage only - will commit() after each email! """
        additionnal_context = {
            'fetchmail_cron_running': True
        }
        MailThread = self.env['mail.thread']
        for server in self:
            _logger.info('start checking for new emails on %s server %s', server.server_type, server.name)
            additionnal_context['default_fetchmail_server_id'] = server.id
            count, failed = 0, 0
            imap_server = None
            pop_server = None
            connection_type = server._get_connection_type()
            if connection_type == 'imap':
                try:
                    imap_server = server.connect()
                    imap_server.select()
                    from_date = self.env.context.get('from_date')
                    to_date = self.env.context.get('to_date')
                    if from_date and to_date:
                        result, data = imap_server.search(None, f'(UNSEEN SINCE {from_date.strftime("%d-%b-%Y")} BEFORE {to_date.strftime("%d-%b-%Y")})')
                    else:
                        install_date=self.env["ir.model.data"].search([('name', '=', 'model_fetch_mails_between_dates')]).create_date
                        result, data = imap_server.search(None,f'(UNSEEN SINCE {install_date.strftime("%d-%b-%Y")})')

                    for num in data[0].split():
                        res_id = None
                        result, data = imap_server.fetch(num, '(RFC822)')
                        imap_server.store(num, '-FLAGS', '\\Seen')
                        try:
                            res_id = MailThread.with_context(**additionnal_context).message_process(server.object_id.model, data[0][1], save_original=server.original, strip_attachments=
                                                                                                        (not server.attach))
                        except Exception:
                            _logger.info('Failed to process mail from %s server %s.', server.server_type, server.name, exc_info=True)
                            failed += 1
                        imap_server.store(num, '+FLAGS', '\\Seen')
                        self._cr.commit()
                        count += 1
                    _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", count, server.server_type, server.name, (count - failed), failed)
                except Exception as e:
                    if raise_exception:
                        raise ValidationError \
                            (_("Couldn't get your emails. Check out the error message below for more info:\n%s", e)) from e
                    else:
                        _logger.info("General failure when trying to fetch mail from %s server %s.", server.server_type, server.name, exc_info=True)
                finally:
                    if imap_server:
                        try:
                            imap_server.close()
                            imap_server.logout()
                        except (OSError, IMAP4.abort):
                            _logger.warning('Failed to properly finish imap connection: %s.', server.name, exc_info=True)
            elif connection_type == 'pop':
                try:
                    while True:
                        failed_in_loop = 0
                        num = 0
                        pop_server = server.connect()
                        (num_messages, total_size) = pop_server.stat()
                        pop_server.list()
                        for num in range(1, min(MAX_POP_MESSAGES, num_messages) + 1):
                            (header, messages, octets) = pop_server.retr(num)
                            message = (b'\n').join(messages)
                            res_id = None
                            try:
                                res_id = MailThread.with_context(**additionnal_context).message_process \
                                    (server.object_id.model, message, save_original=server.original, strip_attachments=(not server.attach))
                                pop_server.dele(num)
                            except Exception:
                                _logger.info('Failed to process mail from %s server %s.', server.server_type, server.name, exc_info=True)
                                failed += 1
                                failed_in_loop += 1
                            self.env.cr.commit()
                        _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", num, server.server_type, server.name, (num - failed_in_loop), failed_in_loop)
                        # Stop if (1) no more message left or (2) all messages have failed
                        if num_messages < MAX_POP_MESSAGES or failed_in_loop == num:
                            break
                        pop_server.quit()
                except Exception as e:
                    if raise_exception:
                        raise ValidationError \
                            (_("Couldn't get your emails. Check out the error message below for more info:\n%s", e)) from e
                    else:
                        _logger.info("General failure when trying to fetch mail from %s server %s.", server.server_type, server.name, exc_info=True)
                finally:
                    if pop_server:
                        try:
                            pop_server.quit()
                        except OSError:
                            _logger.warning('Failed to properly finish pop connection: %s.', server.name, exc_info=True)
            server.write({'date': fields.Datetime.now()})
        return True

    def fetch_mail_by_dates(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "fetch.mails.between.dates",
            "view_mode":"form",
            "views": [[False, "form"]],
            # "domain": [['id', 'in', self.get_children_department_ids().ids]],
            "name": "OpenWizard",
            "target":"new"
        }