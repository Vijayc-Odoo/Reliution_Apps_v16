# -*- coding: utf-8 -*-
import base64
from odoo import api, fields, models, tools
from odoo.exceptions import ValidationError
from bs4 import BeautifulSoup


class MailMail(models.Model):
    _inherit = "mail.mail"

    is_starred = fields.Boolean(string="Starred Mail", default=False,
                                help="Flag indicating whether the mail is starred.")
    is_done = fields.Boolean(string="Done")
    snoozed_until = fields.Datetime(string="Snoozed Until")
    folder_id = fields.Many2one('mail.folder', string="Folder")
    tag_ids = fields.Many2many('mail.tag', string="Tags")
    is_trashed = fields.Boolean(string="Is Trashed", default=False)
    parent_id = fields.Many2one('mail.mail', string='Parent Mail', help='The parent mail of this thread')
    child_ids = fields.One2many('mail.mail', 'parent_id', string='Child Mails',
                                help='Replies and forwards of this mail')
    thread_id = fields.Many2one('mail.mail', string='Threads', help='Root mail of the thread')
    is_read = fields.Boolean(string="Is Read", default=False)
    # bcc_email = fields.Char(string="BCC Email")
    document_model_id = fields.Many2one('ir.model', string="Document Model")
    document_record_id = fields.Integer(string="Document Record ID")
    mail_template_id = fields.Many2one('mail.template', string="Template")
    active = fields.Boolean(default=True, help="Flag indicating whether the mail is active.")
    is_thread_root = fields.Boolean(compute='_compute_is_thread_root', store=True, string="Thread Root")
    mail_message_id = fields.Many2one('mail.message', string="Related Message", ondelete='set null')
    is_odoo_mail = fields.Boolean('Odoo Mail')

    @api.model
    def load_template(self, template_id, doc):
        """Load template content with document context"""
        template = self.env['mail.template'].browse(int(template_id))
        if not template.exists():
            return {}

        model = template.model_id.model
        if not model or not doc:
            return {
                'subject': template.subject or '',
                'body_html': template.body_html or '',
                'attachments': [],
            }

        record = self.env[model].browse(int(doc[0]))
        if not record.exists():
            return {
                'subject': template.subject or '',
                'body_html': template.body_html or '',
                'attachments': [],
            }

        subject = template._render_field('subject', [record.id])[record.id]
        body_html = template._render_field('body_html', [record.id])[record.id]
        plain_text = tools.html_sanitize(body_html)

        attachments = []
        for report in template.report_template_ids:
            pdf_content, _ = report._render_qweb_pdf(report.report_name, [record.id])
            attachments.append({
                'name': f"{report.name}.pdf",
                'datas': base64.b64encode(pdf_content).decode(),
                'mimetype': 'application/pdf',
            })

        return {
            'subject': subject or '',
            'body_html': body_html or '',
            'body_text': plain_text or '',
            'attachments': attachments,
        }

    def _html_to_text(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()

    @api.depends('parent_id')
    def _compute_is_thread_root(self):
        for record in self:
            record.is_thread_root = not bool(record.parent_id)

    @api.model
    def get_mail_count(self):
        """Method to get count of all mails,sent mails
        ,mails in outbox,starred mails and archived mails."""
        user_email = self.env.user.email
        now = fields.Datetime.now()

        all_count = self.sudo().search_count(
            [('create_uid', '=', self.env.user.id), ('is_trashed', '=', False)])
        sent_count = self.sudo().search_count(
            [('create_uid', '=', self.env.user.id), ('state', '=', 'sent'), ('is_trashed', '=', False)])
        outbox_count = self.sudo().search_count(
            [('state', '=', 'exception'),
             ('create_uid', '=', self.env.user.id)])
        stared_count = self.sudo().search_count(
            [('is_starred', '=', True), ('create_uid', '=', self.env.user.id), ('is_trashed', '=', False)])
        archived_count = self.sudo().search_count(
            [('active', '=', False), ('create_uid', '=', self.env.user.id), ('is_trashed', '=', False)])
        trash_count = self.sudo().search_count(
            [('is_trashed', '=', True), ('create_uid', '=', self.env.user.id)])
        inbox_count = self.sudo().search_count(
            [('create_uid', '=', self.env.user.id)])
        done_count = self.sudo().search_count([
            '|',
            ('email_to', 'ilike', user_email), ('recipient_ids.email', 'ilike', user_email), ('is_trashed', '=', False),
            ('is_done', '=', True)
        ])
        # snoozed_count = self.sudo().search_count([
        #     '|',
        #     ('email_to', 'ilike', user_email),('recipient_ids.email', 'ilike', user_email),('is_trashed', '=', False),
        #     ('snoozed_until', '>', now)
        # ])

        mail_dict = {'all_count': all_count,
                     'sent_count': sent_count,
                     'outbox_count': outbox_count,
                     'starred_count': stared_count,
                     'archived_count': archived_count,
                     'trash_count': trash_count,
                     'inbox_count': inbox_count,
                     'done_count': done_count,
                     # 'snoozed_count': snoozed_count
                     }
        return mail_dict

    def mail_user(self):
        user = self.env['res.user']
        mail = user.sudo().search([('create_uid', '=',)])

    @api.model
    def get_starred_mail(self):
        """Method to fetch all starred mails."""
        mails = self.sudo().search(
            [('is_starred', '=', True), ('create_uid', '=', self.env.user.id)])
        return mails.read()

    # @api.model
    # def delete_mail(self, ids):
    #     # """Method to unlink mail."""
    #     """Move mails to Trash instead of deleting."""
    #     mails = self.sudo().search(
    #         [('id', 'in', ids), ('create_uid', '=', self.env.user.id), '|',
    #          ('active', '=', False), ('id', 'in', ids),
    #          ('create_uid', '=', self.env.user.id)])
    #     for mail in mails:
    #         mail.is_trashed = True
    #         mail.active = True
    # mail.sudo().unlink()

    # @api.model
    # def get_trash_mail(self):
    #     """Method to get trashed mails."""
    #     mail_dict = {}
    #     mails = self.sudo().search([
    #         ('is_trashed', '=', True),
    #         ('create_uid', '=', self.env.user.id)
    #     ])
    #     for record in mails:
    #         mail_dict[str(record.mail_message_id)] = {
    #             "id": record.id,
    #             "sender": record.email_to or record.recipient_ids.name,
    #             "subject": record.subject,
    #             "date": fields.Date.to_date(record.create_date),
    #         }
    #     return mails.read()

    @api.model
    def open_mail(self, *args):
        """Method to open a mail and show its content."""
        detail = self.sudo().search(
            [('id', '=', *args), ('create_uid', '=', self.env.user.id), '|',
             ('active', '=', False), ('id', '=', *args),
             ('create_uid', '=', self.env.user.id)]).body_html
        return detail

    # @api.model
    # def archive_mail(self, *args):
    #     """Method to archive mail."""
    #     """Call thay che js mathi and """
    #     self.sudo().search([('id', '=', *args),
    #                         ('create_uid', '=', self.env.user.id)]). \
    #         write({"active": False})

    # @api.model
    # def get_archived_mail(self):
    #     """Method to get archived mails"""
    #     mail_dict = {}
    #     mails = self.sudo().search([('active', '=', False),('is_trashed', '=', False),
    #                                 ('create_uid', '=', self.env.user.id)])
    #     for record in mails:
    #         if record.email_to:
    #             mail_dict[str(record.mail_message_id)] = ({
    #                 "id": record.id,
    #                 "sender": record.email_to,
    #                 "subject": record.subject,
    #                 "date": fields.Date.to_date(record.create_date), })
    #         elif record.recipient_ids:
    #             mail_dict[str(record.mail_message_id)] = ({
    #                 "id": record.id,
    #                 "sender": record.recipient_ids.name,
    #                 "subject": record.subject,
    #                 "date": fields.Date.to_date(record.create_date), })
    #     return mails.read()

    # @api.model
    # def unarchive_mail(self, *args):
    #     """Method to make mail unarchived."""
    #     self.sudo().search([('active', '=', False), ('id', '=', *args),
    #                         ('create_uid', '=', self.env.user.id)]). \
    #         write({'active': True})

    # @api.model
    # def delete_checked_mail(self, *args):
    #     """Method to delete checked mails."""
    #     self.search(
    #         [('id', '=', *args), '|', ('id', '=', *args),
    #          ('active', '=', False)]).sudo().unlink()

    # @api.model
    # def archive_checked_mail(self, *args):
    #     """Method to archive checked mails."""
    #     self.sudo().search([('id', 'in', *args),
    #                         ('create_uid', '=', self.env.user.id)]). \
    #         write({"active": False})

    @api.model
    def mark_done(self, mail_ids):
        if not mail_ids:
            return True
        mails = self.sudo().browse(mail_ids)
        mails.write({'is_done': True})
        return True

    @api.model
    def mark_undone(self, mail_ids):
        mails = self.sudo().browse(mail_ids)
        mails.write({'is_done': False})
        return True

    # @api.model
    # def snooze_mail(self, mail_id, snoozed_until):
    #     mail = self.sudo().browse(mail_id)
    #     mail.snoozed_until = snoozed_until
    #     return True

    # @api.model
    # def unsnooze_mail(self, mail_id):
    #     mail = self.sudo().browse(mail_id)
    #     mail.snoozed_until = False
    #     return True

    @api.model
    def get_mail_folders(self):
        folders = self.env['mail.folder'].sudo().search([])
        return [{'id': f.id, 'name': f.name} for f in folders]

    @api.model
    def sent_mail(self, *args, **kwargs):
        """Method to compose and send mail."""
        attachment_ids = []
        mail_from = self.env.user.email
        subject = kwargs.get('subject')
        recipient = kwargs.get('recipient')
        cc = kwargs.get('cc')
        document_model = kwargs.get('document_model')
        document_id = kwargs.get('document_id')
        if document_model and not document_id:
            raise ValidationError("Please select a record for the chosen document type")

        content = kwargs.get('content')
        image = kwargs.get('images')

        # partner = self.env['res.partner'].search([('email', '=', recipient)], limit=1)
        # if not partner:
        #     partner = self.env['res.partner'].create({
        #         'name': recipient.split('@')[0],  # Use the local-part of the email as name
        #         'email': recipient,
        #     })
        # Process recipients - create partners if needed
        recipient_emails = [r.strip() for r in recipient.split(',') if r.strip()]
        partner_ids = []
        for email in recipient_emails:
            partner = self.env['res.partner'].search([('email', '=', email)], limit=1)
            if not partner:
                partner = self.env['res.partner'].create({
                    'name': email.split('@')[0],
                    'email': email,
                })
            partner_ids.append(partner.id)

        if not document_id and not document_model:
            document_id = partner.id
            document_model = 'res.partner'

        if image:
            for img_data in image:
                image_data = img_data.get('image_uri')
                if image_data:
                    attachment = self.env['ir.attachment'].create({
                        'name': img_data.get('name'),
                        'datas': image_data,
                    })
                    attachment_ids.append((4, attachment.id))
        message_vals = {
            'subject': subject,
            'body': content,
            'email_from': mail_from,
            'email_msg_to': recipient,
            'email_msg_cc': cc,
            'model': document_model,
            'res_id': int(document_id),
            'message_type': 'email_outgoing',
            'attachment_ids': attachment_ids,
            'subtype_id': self.env.ref('mail.mt_comment').id,
            'partner_ids': [(6, 0, [self.env.user.partner_id.id])],
            'is_odoo_mail_message': True,
        }
        message = self.env['mail.message'].create(message_vals)

        mail_id = self.sudo().with_user(user=self.env.user).create({
            "subject": subject,
            "email_to": recipient,
            "email_cc": cc,
            "email_from": mail_from,
            "body_html": content,
            "attachment_ids": attachment_ids,
            "document_model_id": self.env['ir.model']._get(document_model).id if document_model else False,
            "document_record_id": document_id,
            "mail_message_id": message.id,
            "is_odoo_mail": True,
        })

        mail_id.send()
        return mail_id.read()

    @api.model
    def retry_mail(self, *args):
        """Method to retry failed messages"""
        mail = self.search([('id', '=', int(*args)),
                            ('create_uid', '=', self.env.user.id)])
        mail.mark_outgoing()
        mail.send()

    # @api.model
    # def restore_mail(self, ids):
    #     """Restore mail from trash."""
    #     mails = self.sudo().search([('id', 'in', ids)])
    #     mails.write({'is_trashed': False})

    @api.model
    def get_done_mails(self):
        user_email = self.env.user.email
        done_mails = self.sudo().search([
            '|',
            '|',
            ('email_from', 'ilike', user_email),
            ('email_to', 'ilike', user_email),
            ('recipient_ids.email', 'ilike', user_email),
            ('is_trashed', '=', False),
            ('is_done', '=', True)
        ], order='create_date desc')
        return done_mails.read()

    # @api.model
    # def get_snoozed_mails(self):
    #     user_email = self.env.user.email
    #     now = fields.Datetime.now()
    #     snoozed_mails = self.sudo().search([
    #         '|',
    #         ('email_to', 'ilike', user_email),
    #         ('recipient_ids.email', 'ilike', user_email),
    #         ('is_trashed', '=', False),
    #         ('snoozed_until', '>', now)
    #     ], order='snoozed_until asc')
    #     return snoozed_mails.read()

    # @api.model
    # def get_inbox_mails(self):
    #     """Return only top-level, not-done, not-trashed mails addressed to the current user."""
    #     user_email = self.env.user.email
    #     now = fields.Datetime.now()
    #
    #     inbox_mails = self.sudo().search([
    #         '|',
    #         '|',
    #         ('email_from', 'ilike', user_email),
    #         ('email_to', 'ilike', user_email),
    #         ('recipient_ids.email', 'ilike', user_email),
    #         ('is_trashed', '=', False),
    #         ('is_done', '=', False),
    #         ('mail_message_id.child_ids', '!=', False),
    #         ('is_odoo_mail', '=', True),
    #     ], order='create_date desc')
    #     return inbox_mails.read()

    @api.model
    def get_mail_thread(self, mail_id):
        """Return every message (out + in) of the conversation, oldest → newest."""
        mail_msg = self.env['mail.message']
        MailMail = self.env['mail.mail']

        parent_mail = mail_msg.browse(mail_id)
        if not parent_mail:
            return []
        root_msg = parent_mail
        while root_msg.parent_id:
            root_msg = root_msg.parent_id

        def _walk(msg):
            res = [msg]
            for child in msg.child_ids:
                res += _walk(child)
            return res

        all_msgs = _walk(root_msg)  # mail.message objects
        all_msgs.sort(key=lambda m: m.date or m.create_date)

        # ── 3.  Build a unified thread list  ─────────────────────────────────────────
        allowed_types = {'email', 'comment', 'email_outgoing'}
        thread = []
        for msg in all_msgs:
            if msg.message_type in allowed_types:
                thread.append({
                    'id': f"msg-{msg.id}",  # ensure unique key for JS
                    'subject': msg.subject,
                    'email_from': msg.email_from,
                    'email_to': msg.email_msg_to if msg.email_msg_to else ', '.join(
                        [partner.email_formatted for partner in msg.partner_ids]),
                    # 'email_to': ','.join(msg.email_to.split(',')) if msg.email_to else '',
                    'email_cc': msg.email_msg_cc,
                    'body_html': msg.body,
                    'create_date': msg.date or msg.create_date,
                    'attachment_ids': msg.attachment_ids.ids,
                })

        return thread

    @api.model
    def reply_mail(self, mail_id, reply_content, attachments=None, cc=None):
        original_message = None
        if isinstance(mail_id, str) and mail_id.startswith('msg-'):
            mail_record_id = int(mail_id.replace('msg-', ''))
            record = self.mail_message_id.sudo().browse(mail_record_id)
            original_message = record
        else:
            record = self.sudo().browse(mail_id)
            original_message = record.mail_message_id

        original = record

        if not original:
            return []

        body_html = None
        if isinstance(mail_id, str) and mail_id.startswith('msg-'):
            body_html = (
                    reply_content.replace('\n', '<br>')
                    + f"<br><br>On {original.create_date}, {original.email_from} wrote:"
                    + f"<blockquote>{original.body or ''}</blockquote>"
            )
        else:
            body_html = (
                    reply_content.replace('\n', '<br>')
                    + f"<br><br>On {original.create_date}, {original.email_from} wrote:"
                    + f"<blockquote>{original.body_html or ''}</blockquote>"
            )
        reply_subject = f"Re: {original.subject or ''}"
        recipient = original.email_from

        attachment_ids = []
        if attachments:
            for attachment in attachments:
                attachment_data = {
                    'name': attachment.get('name'),
                    'datas': attachment.get('datas'),
                    'res_model': 'mail.message',
                    'res_id': 0,
                }
                if attachment.get('mimetype'):
                    attachment_data['mimetype'] = attachment.get('mimetype')
                attachment = self.env['ir.attachment'].create(attachment_data)
                attachment_ids.append((4, attachment.id))

        msg_vals = {
            'subject': reply_subject,
            'body': body_html,
            'email_from': self.env.user.email,
            'email_msg_to': original.email_from,
            'email_msg_cc': cc,
            'message_type': 'email_outgoing',
            'model': original.model,
            'res_id': original.res_id,
            'parent_id': original_message.id,
            'subtype_id': self.env.ref('mail.mt_comment').id,
            'partner_ids': [(6, 0, [self.env.user.partner_id.id])],
            'attachment_ids': attachment_ids,
            # 'is_odoo_mail_message': True
        }
        msg = self.env['mail.message'].create(msg_vals)

        mail_vals = {
            'subject': reply_subject,
            'email_to': recipient,
            'email_from': self.env.user.email,
            'email_cc': cc,
            'body_html': body_html,
            # 'parent_id': original.id,
            # 'thread_id': original.thread_id.id or original.id,
            'mail_message_id': msg.id,
            'attachment_ids': attachment_ids,
            # 'document_model_id': original.document_model_id.id,
            # 'document_record_id': original.document_record_id,
        }
        reply_mail = self.create(mail_vals)
        reply_mail.send()
        return reply_mail.read()

    @api.model
    def forward_mail(self, mail_id, forward_recipient, forward_content, attachment_ids=None, new_attachment_ids=None,
                     cc=None):
        """Compose a forward of a mail."""
        parent_id = None
        if isinstance(mail_id, str) and mail_id.startswith('msg-'):
            mail_record_id = int(mail_id.replace('msg-', ''))
            record = self.mail_message_id.sudo().browse(mail_record_id)
            parent_id = record
        else:
            record = self.sudo().browse(mail_id)
            parent_id = record.mail_message_id

        original_mail = record

        if not original_mail:
            return []

        body_html = None
        if isinstance(mail_id, str) and mail_id.startswith('msg-'):
            quoted_content = (
                f"<br><br>---------- Forwarded message ----------<br>"
                f"From: {original_mail.email_from}<br>"
                f"Date: {original_mail.create_date}<br>"
                f"Subject: {original_mail.subject}<br>"
                # f"To: {original_mail.email_to}<br>"
                f"<blockquote>{original_mail.body}</blockquote>"
            )
            body_html = forward_content.replace('\n', '<br>') + quoted_content

        else:
            quoted_content = (
                f"<br><br>---------- Forwarded message ----------<br>"
                f"From: {original_mail.email_from}<br>"
                f"Date: {original_mail.create_date}<br>"
                f"Subject: {original_mail.subject}<br>"
                f"To: {forward_recipient}<br>"
                f"<blockquote>{original_mail.body_html}</blockquote>"
            )
            body_html = forward_content.replace('\n', '<br>') + quoted_content

        subject = f"Fwd: {original_mail.subject or ''}"
        recipient = forward_recipient

        msg_vals = {
            'subject': subject,
            'body': body_html,
            'email_from': self.env.user.email,
            'email_msg_to': recipient,
            'email_msg_cc': cc,
            'message_type': 'email_outgoing',
            'model': original_mail.model,
            'res_id': original_mail.res_id,
            'parent_id': parent_id.id,
            'subtype_id': self.env.ref('mail.mt_comment').id,
            'partner_ids': [(6, 0, [self.env.user.partner_id.id])],
            # 'is_odoo_mail_message': True
        }
        msg = self.env['mail.message'].create(msg_vals)

        # Handle attachments
        attachment_vals = []

        # Add existing attachments
        if attachment_ids:
            for attachment_id in attachment_ids:
                original_attachment = self.env['ir.attachment'].browse(attachment_id)
                if original_attachment:
                    new_attachment = original_attachment.copy({
                        'res_model': 'mail.message',
                        'res_id': msg.id,
                    })
                    attachment_vals.append((4, new_attachment.id))

        # Add new attachments
        # if new_attachment_ids:
        #     for attachment_id in new_attachment_ids:
        #         attachment_vals.append((4, attachment_id))
        if new_attachment_ids:
            for att in new_attachment_ids:
                if att.get('datas') and att.get('name'):
                    attachment = self.env['ir.attachment'].create({
                        'name': att.get('name'),
                        'datas': att.get('datas'),
                        'mimetype': att.get('mimetype', 'application/octet-stream'),
                        'res_model': 'mail.message',
                        'res_id': msg.id,
                    })
                    if attachment.id:
                        attachment_vals.append((4, attachment.id))

        if attachment_vals:
            msg.write({'attachment_ids': attachment_vals})

        mail_vals = {
            'subject': subject,
            'email_to': recipient,
            'email_from': self.env.user.email,
            'email_cc': cc,
            'body_html': body_html,
            # 'parent_id': original_mail.id,
            # 'thread_id': original.thread_id.id or original.id,
            'mail_message_id': msg.id,
            # 'document_model_id': original.document_model_id.id,
            # 'document_record_id': original.document_record_id,
        }
        forward_mail = self.create(mail_vals)
        forward_mail.send()
        return forward_mail.read()


class MailMessage(models.Model):
    _inherit = 'mail.message'

    is_odoo_mail_message = fields.Boolean('Odoo mail message')
    email_msg_to = fields.Char('To', help='Message recipients (emails_message)')
    email_msg_cc = fields.Char('Cc')
    is_read = fields.Boolean(string="Is Read", default=False)
    is_starred = fields.Boolean(string="Starred Mail", default=False,
                                help="Flag indicating whether the mail is starred.")
    is_trashed = fields.Boolean(string="Is Trashed", default=False)
    active = fields.Boolean(default=True, help="Flag indicating whether the mail is active.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('message_type') in ['comment', 'email']:
                vals['is_odoo_mail_message'] = True
        return super(MailMessage, self).create(vals_list)

    @api.model
    def mark_as_read(self, mail_ids):
        mail_ids = mail_ids if isinstance(mail_ids, (list, tuple)) else [mail_ids]
        self.browse(mail_ids).write({'is_read': True})
        return True

    @api.model
    def mark_as_unread(self, mail_ids):
        mail_ids = mail_ids if isinstance(mail_ids, (list, tuple)) else [mail_ids]
        self.browse(mail_ids).write({'is_read': False})
        return True

    @api.model
    def star_mail(self, *args):
        """Method to make a mail starred."""
        self.search([('id', '=', *args),
                     ('create_uid', '=', self.env.user.id)]).write({"is_starred": True})

    @api.model
    def unstar_mail(self, *args):
        """Method to make a mail not starred."""
        self.sudo().search([('id', '=', *args),
                            ('create_uid', '=', self.env.user.id)]).write({"is_starred": False})

    @api.model
    def get_inbox_mails(self):
        """Return only top-level, not-done, not-trashed mails addressed to the current user."""
        user_email = self.env.user.email
        now = fields.Datetime.now()

        domain = [
            ('parent_id', '=', False),
            # ('child_ids', '!=', False),
            ('is_trashed', '=', False),
            ('is_odoo_mail_message', '=', True),
            '|',
            '|',
            ('email_from', 'ilike', user_email),
            ('email_msg_to', 'ilike', user_email),
            ('partner_ids', 'in', self.env.user.partner_id.ids),
        ]

        parent_messages = self.sudo().search(domain)
        # parent_messages = self.sudo().search([('is_odoo_mail_message', '=', True),('parent_id','=',False)])

        result = parent_messages.filtered(
            lambda msg:not msg.message_type == 'email_outgoing' and not msg.parent_id or any(
                child.message_type == 'email'
                for child in msg.child_ids
            )
        )
        # result = parent_messages.filtered(
        #     lambda msg: any(
        #         child.message_type == 'email'
        #         for child in msg.child_ids
        #     )
        # )
        # result = parent_messages.filtered(lambda m: m.message_type == 'email')

        # return parent_messages
        return result.read()

        # inbox_mails = self.sudo().search([
        #     '|',
        #     '|',
        #     ('email_from', 'ilike', user_email),
        #     ('email_msg_to', 'ilike', user_email),
        #     ('partner_ids.email', 'ilike', user_email),
        #     ('is_trashed', '=', False),
        #     # ('is_done', '=', False),
        #     ('child_ids', '!=', False),
        #     # ('message_type', '=', 'email'),
        #     ('is_odoo_mail_message', '=', True),
        # ], order='create_date desc')
        # return inbox_mails.read()

    @api.model
    def delete_mail(self, ids):
        # """Method to unlink mail."""
        """Move mails to Trash instead of deleting."""
        mails = self.sudo().search(
            [('id', 'in', ids), ('create_uid', '=', self.env.user.id), '|',
             ('active', '=', False), ('id', 'in', ids),
             ('create_uid', '=', self.env.user.id)])
        for mail in mails:
            mail.is_trashed = True
            mail.active = True

    @api.model
    def get_trash_mail(self):
        """Method to get trashed mails."""
        mail_dict = {}
        mails = self.sudo().search([
            ('is_trashed', '=', True),
            ('create_uid', '=', self.env.user.id)
        ])
        for record in mails:
            mail_dict[str(record)] = {
                "id": record.id,
                "sender": record.email_msg_to or ", ".join(
                    record.partner_ids.mapped('name')) if record.partner_ids else False,
                "subject": record.subject,
                "date": fields.Date.to_date(record.create_date),
            }
        return mails.read()

    @api.model
    def restore_mail(self, ids):
        """Restore mail from trash."""
        mails = self.sudo().search([('id', 'in', ids)])
        mails.write({'is_trashed': False})

    @api.model
    def delete_forever_mail(self, *args):
        """Method to delete forever mails."""
        self.search(
            [('id', '=', *args), '|', ('id', '=', *args), ('active', '=', False)]).sudo().unlink()

    # @api.model
    # def delete_checked_mail(self, *args):
    #     """Method to delete checked mails."""
    #     self.search(
    #         [('id', '=', *args), '|', ('id', '=', *args), ('active', '=', False)]).sudo().unlink()

    @api.model
    def archive_mail(self, *args):
        """Method to archive mail."""
        """Call thay che js mathi and """
        self.sudo().search([('id', '=', *args), ('create_uid', '=', self.env.user.id)]).write({"active": False})

    @api.model
    def get_archived_mail(self):
        """Method to get archived mails"""
        mail_dict = {}
        mails = self.sudo().search([('active', '=', False), ('is_trashed', '=', False),
                                    ('create_uid', '=', self.env.user.id)])
        for record in mails:
            if record.email_msg_to:
                mail_dict[str(record)] = ({
                    "id": record.id,
                    "sender": record.email_msg_to,
                    "subject": record.subject,
                    "date": fields.Date.to_date(record.create_date), })
            elif record.partner_ids:
                mail_dict[str(record)] = ({
                    "id": record.id,
                    "sender": ", ".join(record.partner_ids.mapped('name')) if record.partner_ids else False,
                    "subject": record.subject,
                    "date": fields.Date.to_date(record.create_date), })
        return mails.read()

    @api.model
    def unarchive_mail(self, *args):
        """Method to make mail unarchived."""
        self.sudo().search([('active', '=', False), ('id', '=', *args),
                            ('create_uid', '=', self.env.user.id)]). \
            write({'active': True})

    # @api.model
    # def delete_checked_mail(self, *args):
    #     """Method to delete checked mails."""
    #     self.search(
    #         [('id', '=', *args), '|', ('id', '=', *args),
    #          ('active', '=', False)]).sudo().unlink()

    @api.model
    def delete_checked_mail(self, *args):
        """Method to delete checked mails."""
        mails = self.sudo().search(
            [('id', '=', *args), '|', ('id', '=', *args),
             ('active', '=', False)])

        for mail in mails:
            mail.is_trashed = True
            mail.active = True

    @api.model
    def archive_checked_mail(self, *args):
        """Method to archive checked mails."""
        self.sudo().search([('id', 'in', *args),
                            ('create_uid', '=', self.env.user.id)]). \
            write({"active": False})


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def get_current_user_id(self):
        return self.env.user.id


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    _mail_flat_thread = False

    def _message_compute_parent_id(self, parent_id):
        return super()._message_compute_parent_id(parent_id)
