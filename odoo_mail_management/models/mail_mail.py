# -*- coding: utf-8 -*-
import base64
from odoo import api, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.tools import format_datetime

from datetime import datetime

from bs4 import BeautifulSoup


class MailMail(models.Model):
    _inherit = "mail.mail"

    is_starred = fields.Boolean(string="Starred Mail", default=False,
                                help="Flag indicating whether the mail is starred.")
    is_done = fields.Boolean(string="Done")
    snoozed_until = fields.Datetime(string="Snoozed Until")
    folder_id = fields.Many2one('mail.folder', string="Folder")
    tag_ids = fields.Many2many('mail.tag', string="Tags")
    trashed = fields.Boolean(string="Is Trashed", default=False)
    parent_id = fields.Many2one('mail.mail', string='Parent Mail', help='The parent mail of this thread')
    child_ids = fields.One2many('mail.mail', 'parent_id', string='Child Mails',
                                help='Replies and forwards of this mail')
    thread_id = fields.Many2one('mail.mail', string='Threads', help='Root mail of the thread')
    is_read = fields.Boolean(string="Is Read")
    document_model_id = fields.Many2one('ir.model', string="Document Model")
    document_record_id = fields.Integer(string="Document Record ID")
    mail_template_id = fields.Many2one('mail.template', string="Template")
    is_active = fields.Boolean(help="Flag indicating whether the mail is active.")
    archived= fields.Boolean(help="Flag indicating whether the mail is archived.")
    mail_message_id = fields.Many2one('mail.message', string="Related Message", ondelete='set null')
    is_odoo_mail = fields.Boolean('Odoo Mail')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['is_active'] = True
        return super(MailMail, self).create(vals_list)

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
        try:
            for report in template.report_template_ids:
                pdf_content, _ = report._render_qweb_pdf(report.report_name, [record.id])
                attachments.append({
                    'name': f"{report.name}.pdf",
                    'datas': base64.b64encode(pdf_content).decode(),
                    'mimetype': 'application/pdf',
                })
        except Exception:
            print(Exception)

        return {
            'subject': subject or '',
            'body_html': body_html or '',
            'body_text': plain_text or '',
            'attachments': attachments,
        }

    def _html_to_text(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()

    @api.model
    def get_mail_count(self):
        """Method to get count of all mails,sent mails
        ,mails in outbox,starred mails and archived mails."""
        user_email = self.env.user.email
        now = fields.Datetime.now()

        all_count = self.sudo().search_count(
            [('create_uid', '=', self.env.user.id), ('trashed', '=', False)])
        sent_count = self.sudo().search_count(
            [('create_uid', '=', self.env.user.id), ('state', '=', 'sent'), ('trashed', '=', False),('archived','=', False)])
        outbox_count = self.sudo().search_count(
            [('state', '=', 'exception'),
             ('create_uid', '=', self.env.user.id)])
        stared_count = self.sudo().search_count(
            [('is_starred', '=', True), ('create_uid', '=', self.env.user.id), ('trashed', '=', False),('archived','=', False)])
        archived_count = self.sudo().search_count(
            [('archived', '=', True), ('create_uid', '=', self.env.user.id), ('trashed', '=', False),('archived','=', True)])
        trash_count = self.sudo().search_count(
            [('trashed', '=', True), ('create_uid', '=', self.env.user.id)])
        inbox_count = self.sudo().search_count(
            [('create_uid', '=', self.env.user.id)])
        done_count = self.sudo().search_count([
            '|',
            ('email_to', 'ilike', user_email), ('recipient_ids.email', 'ilike', user_email), ('trashed', '=', False),
            ('is_done', '=', True)
        ])


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

    @api.model
    def open_mail(self, *args):
        """Method to open a mail and show its content."""
        detail = self.sudo().search(
            [('id', '=', *args), ('create_uid', '=', self.env.user.id), '|',
             ('is_active', '=', False), ('id', '=', *args),
             ('create_uid', '=', self.env.user.id)]).body_html
        return detail

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

    @api.model
    def get_done_mails(self):
        user_email = self.env.user.email
        done_mails = self.sudo().search([
            '|',
            '|',
            ('email_from', 'ilike', user_email),
            ('email_to', 'ilike', user_email),
            ('recipient_ids.email', 'ilike', user_email),
            ('trashed', '=', False),
            ('is_done', '=', True)
        ], order='create_date desc')
        return done_mails.read()

    @api.model
    def get_mail_thread(self, mail_id,id=False):
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
        if id:
            ids = [rec.id for rec in all_msgs]
            return ids
        # ── 3.  Build a unified thread list  ─────────────────────────────────────────
        allowed_types = {'email', 'comment', 'email_outgoing'}
        thread = []
        for msg in all_msgs:
            if msg.message_type in allowed_types:
                thread.append({
                    'message_type':msg.message_type,
                    'id': f"msg-{msg.id}",  # ensure unique key for JS
                    'subject': msg.subject,
                    'main_subject':parent_mail.subject,
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

        # convert time current user timezone
        dt = fields.Datetime.from_string(original.create_date)
        user_tz = self.env.user.tz or 'UTC'
        mail_date = format_datetime(self.env, dt, tz=user_tz)

        body_html = None
        if isinstance(mail_id, str) and mail_id.startswith('msg-'):
            body_html = (
                    reply_content.replace('\n', '<br>')
                    + f"<br><br>On {mail_date}, {original.email_from} wrote:"
                    + f"<blockquote>{original.body or ''}</blockquote>"
            )
        else:
            body_html = (
                    reply_content.replace('\n', '<br>')
                    + f"<br><br>On {mail_date}, {original.email_from} wrote:"
                    + f"<blockquote>{original.body_html or ''}</blockquote>"
            )
        reply_subject = f"{original.subject or ''}"
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

        email_msg_to=""
        if original.message_type == 'email':
            email_msg_to=original.email_from
        else:
            email_msg_to=original.email_msg_to

        msg_vals = {
            'subject': reply_subject,
            'body': body_html,
            'email_from': self.env.user.email,
            'email_msg_to': email_msg_to,
            'email_msg_cc': cc,
            'message_type': 'email_outgoing',
            'model': original.model,
            'res_id': original.res_id,
            'parent_id': original_message.id,
            'subtype_id': self.env.ref('mail.mt_comment').id,
            'partner_ids': [(6, 0, [self.env.user.partner_id.id])],
            'attachment_ids': attachment_ids,
        }
        msg = self.env['mail.message'].create(msg_vals)

        mail_vals = {
            'subject': reply_subject,
            'email_to': email_msg_to,
            'email_from': self.env.user.email,
            'email_cc': cc,
            'body_html': body_html,
            'mail_message_id': msg.id,
            'attachment_ids': attachment_ids,
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
            'mail_message_id': msg.id,
        }
        forward_mail = self.create(mail_vals)
        forward_mail.send()
        return forward_mail.read()


class MailMessage(models.Model):
    _inherit = 'mail.message'

    is_odoo_mail_message = fields.Boolean('Odoo mail message')
    email_msg_to = fields.Char('To', help='Message recipients (emails_message)')
    email_msg_cc = fields.Char('Cc')
    is_read = fields.Boolean(string="Is Read")
    is_starred = fields.Boolean(string="Starred Mail", default=False,
                                help="Flag indicating whether the mail is starred.")
    trashed = fields.Boolean(string="Is Trashed", default=False)
    is_active = fields.Boolean(help="Flag indicating whether the mail is active.")
    archived = fields.Boolean(help="Flag indicating whether the mail is archived.")

    @api.model_create_multi
    def create(self, vals_list):
        is_email_or_comment=False
        for vals in vals_list:
            if vals.get('message_type') in ['comment', 'email']:
                vals['is_odoo_mail_message'] = True
                vals['is_read'] = False
                is_email_or_comment=True
            vals['is_active'] = True
        result= super(MailMessage, self).create(vals_list)

        # This is used to highlight the main mail so that the user can easily identify a new mail.
        if is_email_or_comment and result.parent_id:
            parent = result.parent_id
            while parent.parent_id:
                parent = parent.parent_id
            self.mark_as_unread(parent.id)
            return result
        else:
            return result

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
        self.search([('id', '=', *args)]).sudo().write({"is_starred": True})

    @api.model
    def unstar_mail(self, *args):
        """Method to make a mail not starred."""
        self.search([('id', '=', *args)]).sudo().write({"is_starred": False})

    # This function is used to retrieve the ID of the most recent mail
    # def get_last_child_message(self,msg,mailType=False):
    #     if not mailType:
    #         if msg.child_ids:
    #             # # Find the latest child (by date or ID)
    #             # last_child = max(msg.child_ids, key=lambda m: m.date or m.create_date)
    #             # # Recurse into its children
    #             # return self.get_last_child_message(last_child)
    #             return msg
    #     else:
    #         if mailType and mailType in ['starred', 'allMail']:
    #             if msg.child_ids:
    #                 # Find the latest child (by date or ID)
    #                 last_child = max(msg.child_ids, key=lambda m: m.date or m.create_date)
    #                 # Recurse into its children
    #                 return self.get_last_child_message(last_child)
    #         else:
    #             def collect_email_outgoings(message):
    #                 outgoing_emails = []
    #                 if message.message_type == 'email_outgoing':
    #                     outgoing_emails.append(message)
    #                 for child in message.child_ids:
    #                     outgoing_emails += collect_email_outgoings(child)
    #                 return outgoing_emails
    #
    #             all_outgoing = collect_email_outgoings(msg)
    #             if all_outgoing:
    #                 return max(all_outgoing, key=lambda m: m.date or m.create_date)
    #     return msg

    def get_last_child_message(self, msg, mailType=False, is_sorted_data=False):
        """Return the latest relevant child message based on type."""

        visited = set()

        def _walk(message):
            """Recursively collect all child messages without infinite loops."""
            if message.id in visited:
                return []
            visited.add(message.id)

            res = [message]
            for child in message.child_ids:
                res += _walk(child)
            return res

        # Step 1: Collect the whole thread (msg + all descendants safely)
        all_msgs = _walk(msg)

        # Step 2: Handle specific mailType cases
        if mailType in ['starred', 'allMail']:
            return max(all_msgs, key=lambda m: m.date or m.create_date)

        if mailType not in (False, None, ''):
            outgoing = [m for m in all_msgs if m.message_type == 'email_outgoing']
            if outgoing:
                return max(outgoing, key=lambda m: m.date or m.create_date)

        # Step 3: If sorted_data requested, return latest by ID
        if is_sorted_data:
            return max(all_msgs, key=lambda rec: rec.id)

        # Step 4: Fallback → latest by date
        return max(all_msgs, key=lambda m: m.date or m.create_date)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None,mailType=False, **read_kwargs):
        data = super().search_read(domain)
        if mailType:
            search_data = self.search(domain)
            return self.sorted_mail_data(search_data)
        return data

    def sorted_mail_data(self,result):
        data=result.read(['id', 'subject', 'date', 'preview', 'parent_id', 'child_ids','model', 'res_id', 'message_type', 'email_from', 'author_id', 'partner_ids', 'starred', 'reply_to','is_read', 'is_starred', 'trashed', 'is_active','archived'])
        last=[]
        for index, res in enumerate(result):
            if res.child_ids:
                last_mail_message = self.get_last_child_message(res)
                if last_mail_message.preview:
                    data[index]['Last_Message'] = last_mail_message.preview
                    data[index]['Last_Date'] = last_mail_message.date

                    dt = fields.Datetime.from_string(last_mail_message.date)
                    user_tz = self.env.user.tz or 'UTC'
                    converted_mail_date = format_datetime(self.env, dt, tz=user_tz)

                    data[index]['Last_Message_Date'] = converted_mail_date
            else:
                dt = fields.Datetime.from_string(res.date)
                user_tz = self.env.user.tz or 'UTC'
                converted_mail_date = format_datetime(self.env, dt, tz=user_tz)

                data[index]['Last_Message_Date'] = converted_mail_date

        # Show latest mail in teh top
        sorted_data = sorted(data, key=lambda x:datetime.strptime( x['Last_Message_Date'],"%b %d, %Y, %I:%M:%S %p"), reverse=True)
        # print(test)
        return sorted_data

    @api.model
    def get_inbox_mails(self):
        """Return only top-level, nomzit-done, not-trashed mails addressed to the current user."""
        user_email = self.env.user.email
        now = fields.Datetime.now()

        domain = ['&','&', '&', '&', ('parent_id', '=', False), ('trashed', '=', False), ('is_odoo_mail_message', '=', True),('is_active','=',True),('archived','=',False),
                  '|', '|', ('email_from', 'ilike', user_email), ('email_msg_to', 'ilike', user_email),
                  ('partner_ids', 'in', self.env.user.partner_id.ids)]

        parent_messages = self.sudo().search(domain)

        result = parent_messages.filtered(
            lambda msg:not msg.message_type == 'email_outgoing' and not msg.parent_id or any(
                child.message_type == 'email'
                for child in msg.child_ids
            )
        )

        # user_email = self.env.user.email
        # partner_id = self.env.user.partner_id.id
        #
        # query = """
        #     SELECT DISTINCT *
        #     FROM mail_message mm
        #     LEFT JOIN mail_message_res_partner_rel rel
        #            ON mm.id = rel.mail_message_id
        #     WHERE mm.parent_id IS NULL
        #       AND mm.trashed = FALSE
        #       AND mm.is_odoo_mail_message = TRUE
        #       AND mm.is_active = TRUE
        #       AND (
        #             mm.email_from ILIKE %(email)s
        #          OR mm.email_msg_to ILIKE %(email)s
        #          OR rel.res_partner_id = %(partner_id)s
        #       )
        #       AND (
        #            mm.message_type != 'email_outgoing'
        #            OR EXISTS (
        #                SELECT 1 FROM mail_message child
        #                WHERE child.parent_id = mm.id
        #                  AND child.message_type = 'email'
        #            )
        #       )
        #     ORDER BY mm.id DESC
        #     LIMIT 50
        # """
        #
        # self.env.cr.execute(query, {
        #     "email": f"%{user_email}%",
        #     "partner_id": partner_id,
        # })
        # ids = [row[0] for row in self.env.cr.fetchall()]
        # result = self.env['mail.message'].browse(ids)

        return self.sorted_mail_data(result)

    @api.model
    def delete_mail(self, ids):
        # """Method to unlink mail."""
        """Move mails to Trash instead of deleting."""
        mails = self.sudo().search(
            [('id', 'in', ids), ('create_uid', '=', self.env.user.id), '|',
             ('is_active', '=', False), ('id', 'in', ids),
             ('create_uid', '=', self.env.user.id)])
        for mail in mails:
            mail.trashed = True
            mail.is_active = True

    @api.model
    def get_trash_mail(self):
        """Method to get trashed mails."""
        mail_dict = {}
        # mails = self.sudo().search([('trashed', '=', True),('create_uid', '=', self.env.user.id)])
        mails = self.sudo().search([('trashed', '=', True)])
        for record in mails:
            mail_dict[str(record)] = {
                "id": record.id,
                "sender": record.email_msg_to or ", ".join(
                    record.partner_ids.mapped('name')) if record.partner_ids else "",
                "subject": record.subject,
                "date": fields.Date.to_date(record.create_date),
            }

        return self.sorted_mail_data(mails)

    @api.model
    def restore_mail(self, ids):
        """Restore mail from trash."""
        mails = self.sudo().search([('id', 'in', ids)])
        mails.write({'trashed': False,'archived': False})

    @api.model
    def delete_forever_mail(self, *args):
        """Method to delete forever mails."""
        data=[]
        id=args[0]
        for i in id:
            res=self.env['mail.mail'].get_mail_thread(i,True)
            data.append(res)
        result = [x for sublist in data for x in (sublist if isinstance(sublist, (list, tuple)) else [sublist])]

        # self.search(
        #     [('id', '=', *args), '|', ('id', '=', *args), ('is_active', '=', False)]).sudo().unlink()
        # print(data)
        self.search(
            [('id', '=', result), '|', ('id', '=', result), ('is_active', '=', False)]).sudo().unlink()



    @api.model
    def archive_mail(self, *args):
        """Method to archive mail."""
        """Call thay che js mathi and """
        self.sudo().search([('id', '=', *args)]).write({"archived": True})

    @api.model
    def get_archived_mail(self):
        """Method to get archived mails"""
        mail_dict = {}
        mails = self.sudo().search([('archived', '=', True), ('trashed', '=', False)])
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
                    "sender": ", ".join(record.partner_ids.mapped('name')) if record.partner_ids else "",
                    "subject": record.subject,
                    "date": fields.Date.to_date(record.create_date), })

        return self.sorted_mail_data(mails)

    @api.model
    def unarchive_mail(self, *args):
        """Method to make mail unarchived."""
        self.sudo().search([('archived', '=', True), ('id', '=', *args)]).write({'archived': False})

    @api.model
    def delete_checked_mail(self,*args):
        """Method to delete checked mails."""
        mails = self.sudo().search([('id', '=', *args), '|', ('id', '=', *args),('is_active', '=', False)])

        for mail in mails:
            mail.trashed = True
            mail.is_active = True

    @api.model
    def archive_checked_mail(self, *args):
        """Method to archive checked mails."""
        self.sudo().search([('id', 'in', *args),
                            ('create_uid', '=', self.env.user.id)]). \
            write({"archived": True})


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

class IrModel(models.Model):
    _inherit = 'ir.model'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None,is_compose_mail=False, **read_kwargs):

        if is_compose_mail and len(self.env.company.model_selection_for_email.mapped('id')):
            data=self.search([('id','in',self.env.company.model_selection_for_email.mapped('id'))])
            return data.read()
        return super().search_read(domain,fields,offset,limit,order)