/* @odoo-module*/
import { Component, useRef, useState ,markup, onWillStart } from '@odoo/owl'
import { useService } from "@web/core/utils/hooks";
import { useMailUtils } from './MailUtils.js';
import { formatDateTime } from "@web/core/l10n/dates";

//import { DateTime } from 'luxon';


/**
 * MailBody component for displaying mail details.
 * @extends Component
 */
export class MailBody extends  Component {
    async setup() {
        this.ref = useRef('root');
        this.orm = useService('orm');
        this.mailUtils = useMailUtils();

        this.state = useState({ starred: false });
        this.state.latest_mail=[];
        this.state.date='';
        this.handleSelectAll = (event) => {
            if (this.ref.el) {
                const checkbox = this.ref.el.querySelector(".mail_check_box");
                if (checkbox && this.props.mail.id && event.detail?.visibleMails?.includes(this.props.mail.id)) {
                    checkbox.checked = event.detail.checked;
                    this.props.onSelectMail(this.props.mail.id, event.detail.checked);
                }
            }
        };
        this.env.bus.addEventListener("SELECT:ALL", this.handleSelectAll);
    }

    onWillUnmount() {
        this.env.bus.removeEventListener("SELECT:ALL", this.handleSelectAll);
    }
    /**
     * Method triggered on click of the mail selection checkbox.
     * @param {Object} ev - Event object.
     */
    onClickSelect(ev) {
        const checked = ev.target.checked;
        this.props.onSelectMail(this.props.mail.id, checked);
    }
     /**
     * Method to archive the mail.
     * @param {Object} event - Event object.
     */
     async archiveMail(event){
      var mail = this.props.mail.id
      await this.orm.call('mail.message','archive_mail',[mail])
    }
    /**
     * Method to unarchive the mail.
     * @param {Object} event - Event object.
     */
     async unArchive(event){
      var mail = this.props.mail.id
       await this.orm.call('mail.message','unarchive_mail',[mail])
       window.location.reload();
      }
      /**
     * Method to resend the mail.
     * @param {Object} event - Event object.
     */
    async resendMail(){
      var mail = this.props.mail.id
      await this.orm.call('mail.mail','retry_mail',[mail])
    }
    /**
     * Method to delete the mail.
     * @param {Object} event - Event object.
     */

    async deleteMail(event){
       var mail = this.props.mail.id
       if(this.props.mailType === 'trash'){
        await this.orm.call('mail.message','delete_forever_mail',[mail])
       }
       else{
        await this.orm.call('mail.message','delete_checked_mail',[mail])
       }

       window.location.reload();
    }
    /**
     * Method to star or unstar the mail.
     * @param {Object} event - Event object.
     */
     async starMail(event) {
        const mailId = this.props.mail.id;
        const currentStarred = this.props.mail.is_starred;

        // Toggle star value
        const newStarred = !currentStarred;
        // RPC call to backend
        if (newStarred) {
            await this.orm.call('mail.message', 'star_mail', [mailId]);
        } else {
            await this.orm.call('mail.message', 'unstar_mail', [mailId]);
        }
        this.props.mail.is_starred = newStarred;
    }
    /**
     * Method to open the mail.
     * @param {Object} event - Event object.
     */
   async openMail(event){
     var mail = this.props.mail
     this.props.openMail(mail)
     if (!mail.is_read) {
        await this.markAsRead(mail);
    }
   }

    async toggleDone(mail) {
        mail.is_done = !mail.is_done;
        if (mail.is_done) {
            await this.orm.call('mail.mail', 'mark_done', [mail.id]);
        } else {
            await this.orm.call('mail.mail', 'mark_undone', [mail.id]);
        }
        window.location.reload();
    }
    async markAsRead(mail) {
        if (!mail?.id || mail.is_read) return;
        await this.orm.call('mail.message', 'mark_as_read', [mail.id]);
        mail.is_read = true;
        window.location.reload();
    }

    async markAsUnread(mail) {
        console.log('Incoming:', mail);
        if (!mail?.id || !mail.is_read) {
            console.log('Skipping markAsUnread: mail invalid or already unread');
            return;
        }
        console.log('Proceeding with markAsUnread');
        await this.orm.call('mail.message', 'mark_as_unread', [mail.id]);
        mail.is_read = false;
        window.location.reload();
    }


}
MailBody.template = 'MailBody'




