/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";

//export class SnoozeDialog extends Component {
//    setup() {
//        this.orm = useService("orm");
//        this.state = useState({
//            selectedOption: null,
//            customDate: null,
//            customTime: null
//        });
//    }
//
//    chooseQuickOption(option) {
//        const now = new Date();
//        let snoozeDate;
//
//        switch(option) {
//            case 'later_today':
//                snoozeDate = new Date(now.setHours(now.getHours() + 3));
//                break;
//            case 'tomorrow':
//                snoozeDate = new Date(now.setDate(now.getDate() + 1));
//                break;
//            case 'next_week':
//                snoozeDate = new Date(now.setDate(now.getDate() + 7));
//                break;
//            default:
//                snoozeDate = now;
//        }
//
//        this.state.selectedOption = snoozeDate;
//    }
//
//    onCustomDateChange(ev) {
//        this.state.customDate = ev.target.value;
//    }
//
//    onCustomTimeChange(ev) {
//        this.state.customTime = ev.target.value;
//    }
//
//    async confirmSnooze() {
//        let snoozeDatetime;
//        if (this.state.selectedOption) {
//            snoozeDatetime = this.state.selectedOption;
//        } else if (this.state.customDate && this.state.customTime) {
//            snoozeDatetime = new Date(`${this.state.customDate}T${this.state.customTime}`);
//        } else {
//            alert("Please select a snooze option.");
//            return;
//        }
//
//        await this.orm.call('mail.mail', 'snooze_mail', [this.props.mail.id], {
//            snoozed_until: snoozeDatetime.toISOString()
//        });
//        this.props.close();
//        window.location.reload();
//    }
//
//    closeDialog() {
//        this.props.close();
//    }
//}
//
//SnoozeDialog.template = 'SnoozeDialog';
//SnoozeDialog.components = { Dialog };


