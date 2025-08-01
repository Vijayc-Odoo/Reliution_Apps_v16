/* @odoo-module*/
import { Component } from '@odoo/owl';
import { useService } from "@web/core/utils/hooks";
import { useState, onMounted, markup, useRef, useEnv} from "@odoo/owl";
import { ComposeReplyDialog } from './ComposeReplyDialog.js';
import { ComposeForwardDialog } from './ComposeForwardDialog.js';
import { useMailUtils } from './MailUtils.js';
/**
 * MessageView component for displaying a message.
 * @extends Component
 */
export class MessageView extends  Component {
    setup(){
        debugger;
        this.root = useRef("root-mail")
        this.action = useService("action");
        this.orm = useService("orm");
        this.env = useEnv();
        this.html_content = markup(this.props.mail.body_html)
        this.mailUtils = useMailUtils();
        this.markAsReadOnOpen();
        this.state = useState({
            attachments: {},
            data: [],
            thread: [],

        })
        this.markup = markup;
        this.formatDate = this.formatDate.bind(this);
        this.goBack = this.goBack.bind(this);
        onMounted(this.fetchThread);

    }

    formatDate(date) {
        if (!date) return '';
        return formatDateTime(this.env, date);
    }

    async fetchThread() {
         const thread = await this.orm.call('mail.mail', 'get_mail_thread', [this.props.mail.id]);

         thread.reverse()
        this.state.thread = thread;
        debugger;
        for (const mail of thread) {
            if (mail.attachment_ids && mail.attachment_ids.length) {
                const result = await this.orm.call("ir.attachment", "get_fields", [mail.attachment_ids]);
                this.state.attachments[mail.id] = result;
            }
        }
        debugger;
    }

    onClickImage(value){
     this.action.doAction({
            type: "ir.actions.act_url",
            url: "/web/content/" + value+ "?download=true",
        });
    }
    /**
     * Method to reply the mail.
     */
//    async replyMail() {
//        const replyContent = prompt("Enter your reply:"); // Or use a popup dialog
//        if (replyContent) {
//            await this.orm.call('mail.mail', 'reply_mail', [this.props.mail.id], { reply_content: replyContent });
//            window.location.reload();
//        }
//    }

    async onClickAttachment(attachmentId) {
        this.action.doAction({
            type: "ir.actions.act_url",
            url: `/web/content/${attachmentId}?download=true`,
            target: "self"
        });
    }

    async replyMail(mail, env) {
        debugger;
        env.services.dialog.add(ComposeReplyDialog, {mail: mail});
    }

    async forwardMail(mail, env) {
        env.services.dialog.add(ComposeForwardDialog, {mail: mail});
    }

    async markAsDone() {
        await this.mailUtils.markAsDone(this.props.mail.id);
        window.location.reload(); // optional: reload or navigate back
    }

//    async snoozeMail() {
//        await this.mailUtils.snoozeMail(this.props.mail.id);
//        window.location.reload();
//    }

    async markAsReadOnOpen() {
        if (!this.props.mail?.id || this.props.mail.is_read) return;
        await this.mailUtils.markAsRead(this.props.mail.id);
    }

    async markAsUnread() {
        await this.mailUtils.markAsUnread(this.props.mail.id);
        window.location.reload();
    }

    goBack() {
        if (this.props.onGoBack) {
            this.props.onGoBack();
        } else {
            console.error("No back handler available");
        }
    }
}
MessageView.template = 'MessageView';
MessageView.props = {
    mail: Object,
    onGoBack: { type: Function, optional: true }
};

