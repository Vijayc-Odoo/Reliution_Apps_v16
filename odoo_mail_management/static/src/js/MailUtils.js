/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";

export function useMailUtils() {
    const orm = useService("orm");

    async function markAsDone(mailId) {
        await orm.call('mail.mail', 'mark_done', [mailId]);
    }
    async function markAsUndone(mailId) {
        await orm.call('mail.mail', 'mark_undone', [mailId]);
    }

//    async function snoozeMail(mailId) {
//        const snoozeDate = prompt("Enter snooze date/time in format YYYY-MM-DD HH:MM");
//        if (snoozeDate) {
//            await orm.call('mail.mail', 'snooze_mail', [mailId], { snoozed_until: snoozeDate });
//        }
//    }

    async function markAsRead(mailId) {
            await orm.call('mail.message', 'mark_as_read', [mailId]);
        }

    async function markAsUnread(mailId) {
        await orm.call('mail.message', 'mark_as_unread', [mailId]);
    }

    return {
        markAsDone,
        markAsUndone,
        markAsRead,
        markAsUnread
    };
}
