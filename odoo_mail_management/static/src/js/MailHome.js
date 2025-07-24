/* @odoo-module*/
import { registry } from '@web/core/registry';
import { Component , useRef , useState, onWillStart ,onMounted} from '@odoo/owl'
import { useService, useBus } from "@web/core/utils/hooks";
import { MailBody } from './MailBody'
import { SentMail } from './SentMail'
import { MessageView } from './MessageView'
import { ComposeMail } from './ComposeMail'
import { ImportDialog } from './AttachmentMail'
import { session } from "@web/session";

/**
 * odooMail component for handling mail-related functionalities.
 * @extends Component
 */
class odooMail extends  Component {
    setup() {
        this.mailState = useState({
            loadLogo: "",
            loadMail: [],
            getCount: "",
            outBox: "",
            mode: "list",
            formData: {},
            mailType: "all",
            prevMailType: "allMail",
            currMailType: "allMail",
            totalRecords: 0, // Total records available
            currentPage: 1,  // Current page
            limit: 20, // Number of records to load at once
            offset: 0, // Starting point for loading records
            allRecordsLoaded: false, // Whether all records are loaded
        })
        this.dialogService = useService("dialog")
        this.root = useRef('root');
        this.action = useService('action')
        this.orm = useService('orm')
        this.selectedMails = []
        this.messageViewProps = {
            onGoBack: this.resetView.bind(this)
        };
        onMounted(() => {
            this.allMailView()
        })
        onWillStart(async ()=> {
            this.mailState.loadLogo = await this.orm.call('mail.icon','load_logo',[])
//            this.allMailView()
            this.getCount()
        })
    }

     /**
     * Method to get the count of different mail categories.
     */
    async getCount(){
        this.mailState.getCount = await this.orm.call('mail.mail','get_mail_count',[])
    }
    /**
     * Method to compose a new mail.
     */
    async composeMail(){
     this.dialogService.add(ComposeMail, {
        loadMail: (mail) => {
            this.mailState.loadMail.unshift(mail)
            this.getCount()
        }
     })
    }
    /**
     * Method triggered on click of the "Select All" checkbox.
     * @param {Object} ev - Event object.
     */
    onClickSelectAll(ev) {
        const checked = ev.target.checked;
        const visibleMails = this.mailState.loadMail.map(mail => mail.id);

        if (checked) {
            // Add visible mails
            this.selectedMails = [...new Set([...this.selectedMails, ...visibleMails])];
        } else {
            // Remove visible mails
            this.selectedMails = this.selectedMails.filter(id => !visibleMails.includes(id));
        }
         this.env.bus.trigger("SELECT:ALL", { checked, visibleMails });
        // Trigger bus event to update UI
//        this.env.bus.trigger("SELECT:ALL", { checked })

    }
    /**
     * Getter method to get props for MailBody component.
     * @returns {Object} - Props for MailBody component.
     */
    get mailProps() {
        return {
            onSelectMail: this.onSelectMail.bind(this),
            starMail: this.starMail.bind(this),
            openMail: this.openMail.bind(this),
            mailType: this.mailType,
        }
    }

    async markSelectedAsRead() {
        for (const mailId of this.selectedMails) {
            await this.orm.call('mail.message', 'write', [[mailId], { is_read: true }]);
        }
        this.getCount();
        this.allMailView();
    }

    async markSelectedAsUnread() {
        for (const mailId of this.selectedMails) {
        await this.orm.call('mail.message', 'write', [[mailId], { is_read: false }]);
    }
        this.getCount();
        this.allMailView();
    }
       /**
     * Method to reset the mail view.
     */
    resetView(){
        this.mailState.formData = {}
        this.mailState.mode = "list"
    }
    /**
     * Method to open a specific mail.
     * @param {Object} mail - Mail object.
     */
    openMail(mail) {
        this.mailState.formData = mail
        this.mailState.mode = "form"
    }
     /**
     * Method to star or unstar a mail.
     * @param {Number} mail - Mail ID.
     * @param {Boolean} type - Type of action (star or unstar).
     */
    starMail(mail, type){
        if (type) {
            this.mailState.getCount.starred_count ++
        }
        else this.mailState.getCount.starred_count --
    }
     /**
     * Method triggered on selecting or deselecting a mail.
     * @param {Number} mailId - Mail ID.
     * @param {Boolean} check - Checked or not.
     */
    onSelectMail(mailId, check) {
        if (check) {
            if (!this.selectedMails.includes(mailId)) {
                this.selectedMails.push(mailId);
            }
        } else {
            this.selectedMails = this.selectedMails.filter(item => item !== mailId);
        }
    }
    clearSelections() {
    const selectAllCheckbox = this.root.el.querySelector('#checkall');
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = false;
    }
    this.selectedMails = [];
    const visibleMails = this.mailState.loadMail.map(mail => mail.id);
    this.env.bus.trigger("SELECT:ALL", { checked: false, visibleMails });
    }
    /**
     * Getter method to get the mail type.
     * @returns {String} - Current mail type.
     */
    get mailType() {
        return this.mailState.mailType
    }
      /**
     * Method to archive selected mails.
     * @param {Object} event - Event object.
     */
    //content na header ma aa call thase
    async archiveMail(event){
          if (this.selectedMails.length){
                this.mailState.loadMail = this.mailState.loadMail.filter(item => !this.selectedMails.includes(item.id))
                 await this.orm.call('mail.message','archive_mail',[this.selectedMails])
                 this.getCount()
                 this.clearSelections();
//                 this.selectedMails = []
            }
    }

    async unarchiveMail(event){
          if (this.selectedMails.length){
                this.mailState.loadMail = this.mailState.loadMail.filter(item => !this.selectedMails.includes(item.id))
                 await this.orm.call('mail.message','unarchive_mail',[this.selectedMails])
                 this.getCount()
                 this.clearSelections();
//                 this.selectedMails = []
            }
    }

    async doneMail(event){
          if (this.selectedMails.length){
                this.mailState.loadMail = this.mailState.loadMail.filter(item => !this.selectedMails.includes(item.id))
                 await this.orm.call('mail.mail','mark_done',[this.selectedMails])
                 this.getCount()
                 this.selectedMails = []
                 window.location.reload();
            }
    }

    async undoneMail(event){
          if (this.selectedMails.length){
                this.mailState.loadMail = this.mailState.loadMail.filter(item => !this.selectedMails.includes(item.id))
                 await this.orm.call('mail.mail','mark_undone',[this.selectedMails])
                 this.getCount()
                 this.selectedMails = []
            }
    }
    /**
     * Method to refresh the page.
     * @param {Object} event - Event object.
     */
    refreshPage(event){
      window.location.reload()
    }
     /**
     * Method to delete selected mails.
     * @param {Object} event - Event object.
     */
    async deleteMail(event){
            if (this.selectedMails.length){
                this.mailState.loadMail = this.mailState.loadMail.filter(item => !this.selectedMails.includes(item.id))
                 await this.orm.call('mail.message','delete_checked_mail',[this.selectedMails])
                 this.getCount()
                 this.clearSelections();
//                 this.selectedMails = []
            }
    }

    async delete_forever(event){
            if (this.selectedMails.length){
                this.mailState.loadMail = this.mailState.loadMail.filter(item => !this.selectedMails.includes(item.id))
                 await this.orm.call('mail.message','delete_forever_mail',[this.selectedMails])
                 this.getCount()
                 this.selectedMails = []
            }
    }
 /**
     * Go to the next page of mail records.
     */
    nextPage() {
        if (this.mailState.offset + this.mailState.limit < this.mailState.totalRecords) {
            this.mailState.offset += this.mailState.limit;
            this.mailState.currentPage++;
            this.refreshCurrentView(); // Load new records
            this.addPaginationControls(); // Update controls
        }
    }
    /**
     * Go to the previous page of mail records.
     */
    previousPage() {
        if (this.mailState.offset > 0) {
            this.mailState.offset -= this.mailState.limit;
            this.mailState.currentPage--;
            this.refreshCurrentView();
            this.addPaginationControls();
        }
    }
    refreshCurrentView() {
        if (this.mailState.mailType === 'all') {
            this.allMailView(); // Refresh All Mail view
        } else if (this.mailState.mailType === 'sent') {
            this.sentMail(); // Refresh Sent Mail view
        } else if (this.mailState.mailType === 'starred'){
            this.starredMail() // Refresh Starred Mail view
        } else if(this.mailState.mailType === 'outbox'){
            this.outboxMailView() // Refresh Outbox Mail view
        } else if(this.mailState.mailType === 'archive'){
            this.archivedMail() // Refresh Archive Mail view
        }
    }
    addPaginationControls() {
        const start = this.mailState.offset + 1; // Start index of records being viewed
        const end = Math.min(this.mailState.offset + this.mailState.limit, this.mailState.totalRecords); // End index

        // Update state for reactive template
        this.mailState.recordRange = {
            start: start,
            end: end,
            total: this.mailState.totalRecords,
        };

        // Enable/disable buttons based on current state
        this.mailState.disablePrev = this.mailState.offset === 0;
        this.mailState.disableNext = this.mailState.allRecordsLoaded;
    }

    async restoreMail(event) {
        if (this.selectedMails.length) {
        this.mailState.loadMail = this.mailState.loadMail.filter(item => !this.selectedMails.includes(item.id))
            await this.orm.call('mail.message', 'restore_mail',  [this.selectedMails]);
            this.getCount();
            this.selectedMails = []
            this.trashView();
        }
    }

    async inboxMailView () {
        const root = this.root.el;
        root.querySelector('.inbox')?.classList.add('active');
        root.querySelector('.all_mail')?.classList.remove('active');
        root.querySelector('.sent')?.classList.remove('active');
        root.querySelector('.sent-mail')?.classList.remove('active');
        root.querySelector('.archieved-mail')?.classList.remove('active');
        root.querySelector('.trash-mail')?.classList.remove('active');
        root.querySelector('.outbox')?.classList.remove('active');
        root.querySelector('.done')?.classList.remove('active');
//        root.querySelector('.snoozed')?.classList.remove('active');
        this.mailState.mailType = 'inbox';
        this.resetView();
        const total =  await this.orm.call('mail.message', 'get_inbox_mails', []);
        this.mailState.totalRecords = total.length;
        const paginatedRecords = await this.orm.call('mail.message', 'get_inbox_mails', []);
        const records = paginatedRecords.slice(
            this.mailState.offset,
            this.mailState.offset + this.mailState.limit
        );
        this.mailState.loadMail = records;
        this.mailState.allRecordsLoaded = this.mailState.offset + this.mailState.limit >= this.mailState.totalRecords;
        this.addPaginationControls();
//        this.mailState.loadMail = await this.orm.call('mail.mail', 'get_inbox_mails', []);
    }
    /**
     * Method to view all mails.
     */
     async allMailView() {
             const root = this.root.el;
             root.querySelector('.all_mail')?.classList.add('active');
             root.querySelector('.archieved-mail')?.classList.remove('active');
             root.querySelector('.sent-mail')?.classList.remove('active');
             root.querySelector('.outbox')?.classList.remove('active');
             root.querySelector('.sent')?.classList.remove('active');
             root.querySelector('.trash-mail')?.classList.remove('active');
             root.querySelector('.inbox')?.classList.remove('active');
             root.querySelector('.done')?.classList.remove('active');
//             root.querySelector('.snoozed')?.classList.remove('active');
        this.mailState.mailType = 'all'
        if (this.mailState.currMailType != 'allMail'){
            this.mailState.prevMailType = this.mailState.currMailType
        }
        if (this.mailState.prevMailType != 'allMail' &&  this.mailState.currMailType != 'allMail'){
            this.mailState.offset = 0
        }
        this.mailState.currMailType = 'allMail'
        this.resetView()
        const currentUserId = await this.orm.call('res.users', 'get_current_user_id', []);
        const currentUser = await this.orm.call('res.users', 'read', [[currentUserId], ['email']]);
        const currentUserEmail = currentUser[0].email;
        const domain = [
            ['create_uid', '=', currentUserId],
            ['is_odoo_mail_message', '=', true],
            ['is_trashed', '=', false],
//            ['message_type', 'in', ['comment','email','email_outgoing']],
            ['email_from', 'ilike', currentUserEmail]
        ];
        const total = await this.orm.searchCount('mail.message', domain);
        this.mailState.totalRecords = total;
        const records = await this.orm.call(
            'mail.message', 'search_read',
            [domain, []],
            { limit: this.mailState.limit,
              offset: this.mailState.offset,
              order: "create_date desc" }
        );
        this.mailState.loadMail = records;
        this.mailState.allRecordsLoaded = this.mailState.offset + this.mailState.limit >= this.mailState.totalRecords;
        this.addPaginationControls();
        this.clearSelections();
//        this.mailState.loadMail = await this.orm.searchRead('mail.mail',[['create_uid', '=', this.uid]],[], { order: "create_date desc"})
     }
      /**
     * Method to view starred mails.
     */
    async starredMail(){
        const root = this.root.el;
        root.querySelector('.sent-mail')?.classList.add('active');
        root.querySelector('.archieved-mail')?.classList.remove('active');
        root.querySelector('.outbox')?.classList.remove('active');
        root.querySelector('.sent')?.classList.remove('active');
        root.querySelector('.all_mail')?.classList.remove('active');
        root.querySelector('.trash-mail')?.classList.remove('active');
        root.querySelector('.inbox')?.classList.remove('active');
        root.querySelector('.done')?.classList.remove('active');
//        root.querySelector('.snoozed')?.classList.remove('active');
        this.mailState.mailType = "starred"
        if (this.mailState.currMailType != 'starredMail'){
            this.mailState.prevMailType = this.mailState.currMailType
        }
        if (this.mailState.prevMailType != 'starredMail' &&  this.mailState.currMailType != 'starredMail'){
            this.mailState.offset = 0
        }
        this.mailState.currMailType = 'starredMail'
        this.resetView()
        const currentUserId = await this.orm.call('res.users', 'get_current_user_id', []);
               const domain = [
                ['is_odoo_mail_message', '=', true],
                ['is_trashed', '=', false],
                ['message_type', 'in', ['comment','email','email_outgoing']],
                ['is_starred', '=', true]
        ];
        const total = await this.orm.searchCount('mail.message', domain);
        this.mailState.totalRecords = total;
        const records = await this.orm.call(
            'mail.message', 'search_read',
            [domain, []],
            { limit: this.mailState.limit,
              offset: this.mailState.offset,
              order: "create_date desc" }
        );
        this.mailState.loadMail = records;
        this.mailState.allRecordsLoaded = this.mailState.offset + this.mailState.limit >= this.mailState.totalRecords;
        this.addPaginationControls();
//        this.mailState.loadMail = await this.orm.call('mail.mail','get_starred_mail',[])
    }
     /**
     * Method to view archived mails.
     */
     async archivedMail(){
        const root = this.root.el
        root.querySelector('.archieved-mail')?.classList.add('active');
        root.querySelector('.sent-mail')?.classList.remove('active');
        root.querySelector('.outbox')?.classList.remove('active');
        root.querySelector('.sent')?.classList.remove('active');
        root.querySelector('.all_mail')?.classList.remove('active');
        root.querySelector('.trash-mail')?.classList.remove('active');
        root.querySelector('.inbox')?.classList.remove('active');
        root.querySelector('.done')?.classList.remove('active');
//        root.querySelector('.snoozed')?.classList.remove('active');
        this.mailState.mailType = 'archive'
        if (this.mailState.currMailType != 'archivedMail'){
            this.mailState.prevMailType = this.mailState.currMailType
        }
        if (this.mailState.prevMailType != 'archivedMail' &&  this.mailState.currMailType != 'archivedMail'){
            this.mailState.offset = 0
        }
        this.mailState.currMailType = 'archivedMail'
        this.resetView()
        const total =  await this.orm.call('mail.message', 'get_archived_mail', []);
        this.mailState.totalRecords = total.length;
        const paginatedRecords = await this.orm.call('mail.message','get_archived_mail',[])
        const records = paginatedRecords.slice(
            this.mailState.offset,
            this.mailState.offset + this.mailState.limit
        );
        this.mailState.loadMail = records;
        this.mailState.allRecordsLoaded = this.mailState.offset + this.mailState.limit >= this.mailState.totalRecords;
        this.addPaginationControls();
        this.clearSelections();

//        this.mailState.loadMail = await this.orm.call('mail.mail','get_archived_mail',[])
    }
    /**
    * Method in which deleted mails are move to trash.
    */
    async trashView() {
        const root = this.root.el
        root.querySelector('.trash-mail')?.classList.add('active');
        root.querySelector('.archieved-mail')?.classList.remove('active');
        root.querySelector('.sent-mail')?.classList.remove('active');
        root.querySelector('.outbox')?.classList.remove('active');
        root.querySelector('.sent')?.classList.remove('active');
        root.querySelector('.all_mail')?.classList.remove('active');
        root.querySelector('.inbox')?.classList.remove('active');
        root.querySelector('.done')?.classList.remove('active');
//        root.querySelector('.snoozed')?.classList.remove('active');

        this.mailState.mailType = 'trash';
        if (this.mailState.currMailType != 'trashView'){
            this.mailState.prevMailType = this.mailState.currMailType
        }
        if (this.mailState.prevMailType != 'trashView' &&  this.mailState.currMailType != 'trashView'){
            this.mailState.offset = 0
        }
        this.mailState.currMailType = 'trashView'
        this.resetView();
        const total =  await this.orm.call('mail.message', 'get_trash_mail', []);
        this.mailState.totalRecords = total.length;
        const paginatedRecords = await this.orm.call('mail.message','get_trash_mail',[])
        const records = paginatedRecords.slice(
            this.mailState.offset,
            this.mailState.offset + this.mailState.limit
        );
        this.mailState.loadMail = records;
        this.mailState.allRecordsLoaded = this.mailState.offset + this.mailState.limit >= this.mailState.totalRecords;
        this.addPaginationControls();
        this.clearSelections();
//        this.mailState.loadMail = await this.orm.call('mail.mail', 'get_trash_mail', []);
    }

    async doneMailView() {
        const root = this.root.el;
        root.querySelector('.done')?.classList.add('active');
//        root.querySelector('.snoozed')?.classList.remove('active');
        root.querySelector('.all_mail')?.classList.remove('active');
        root.querySelector('.sent-mail')?.classList.remove('active');
        root.querySelector('.outbox')?.classList.remove('active');
        root.querySelector('.inbox')?.classList.remove('active');
        root.querySelector('.archived-mail')?.classList.remove('active');
        root.querySelector('.trash-mail')?.classList.remove('active');
        root.querySelector('.sent')?.classList.remove('active');

        this.mailState.mailType = 'done';
        if (this.mailState.currMailType != 'doneMailView'){
            this.mailState.prevMailType = this.mailState.currMailType
        }
        if (this.mailState.prevMailType != 'doneMailView' &&  this.mailState.currMailType != 'doneMailView'){
            this.mailState.offset = 0
        }
        this.mailState.currMailType = 'doneMailView'
        this.resetView();
        const total =  await this.orm.call('mail.mail', 'get_done_mails', []);
        this.mailState.totalRecords = total.length;
        const paginatedRecords = await this.orm.call('mail.mail','get_done_mails',[])
        const records = paginatedRecords.slice(
            this.mailState.offset,
            this.mailState.offset + this.mailState.limit
        );
        this.mailState.loadMail = records;
        this.mailState.allRecordsLoaded = this.mailState.offset + this.mailState.limit >= this.mailState.totalRecords;
        this.addPaginationControls();
        this.clearSelections();
//        this.mailState.loadMail = await this.orm.call('mail.mail', 'get_done_mails', []);
    }

//    async snoozedMailView() {
//        const root = this.root.el;
//        root.querySelector('.snoozed')?.classList.add('active');
//        root.querySelector('.done')?.classList.remove('active');
//        root.querySelector('.all_mail')?.classList.remove('active');
//        root.querySelector('.sent-mail')?.classList.remove('active');
//        root.querySelector('.outbox')?.classList.remove('active');
//        root.querySelector('.inbox')?.classList.remove('active');
//        root.querySelector('.archived-mail')?.classList.remove('active');
//        root.querySelector('.trash-mail')?.classList.remove('active');
//
//        this.mailState.mailType = 'snoozed';
//        this.resetView();
//        this.mailState.loadMail = await this.orm.call('mail.mail', 'get_snoozed_mails', []);
//    }
     /**
     * Method to view outbox mails.
     */
    async outboxMailView(){
       const root = this.root.el
       root.querySelector('.outbox')?.classList.add('active');
       root.querySelector('.archieved-mail')?.classList.remove('active');
       root.querySelector('.sent-mail')?.classList.remove('active');
       root.querySelector('.sent')?.classList.remove('active');
       root.querySelector('.all_mail')?.classList.remove('active');
       root.querySelector('.trash-mail')?.classList.remove('active');
       root.querySelector('.inbox')?.classList.remove('active');
       root.querySelector('.done')?.classList.remove('active');
       this.mailState.mailType = "outbox"
       if (this.mailState.currMailType != 'outboxMail'){
       this.mailState.prevMailType = this.mailState.currMailType
        }
        if (this.mailState.prevMailType != 'outboxMail' &&  this.mailState.currMailType != 'outboxMail'){
            this.mailState.offset = 0
        }
        this.mailState.currMailType = 'outboxMail'
       this.resetView()
       const currentUserId = await this.orm.call('res.users', 'get_current_user_id', []);
       const domain = [
            ['create_uid', '=', currentUserId],
            ['state', '=', 'exception'],
        ];
        const total = await this.orm.searchCount('mail.mail', domain, []);
        this.mailState.totalRecords = total;
        const records = await this.orm.call(
            'mail.mail', 'search_read',
            [domain, []],
            { limit: this.mailState.limit,
              offset: this.mailState.offset,
              order: "create_date desc" }
        );
        this.mailState.loadMail = records;
        this.mailState.allRecordsLoaded = this.mailState.offset + this.mailState.limit >= this.mailState.totalRecords;
        this.addPaginationControls();
//       this.mailState.loadMail = await this.orm.searchRead('mail.mail',[['create_uid', '=', currentUserId],['state', '=', 'exception']],[], { order: "create_date desc"})
    }

      /**
     * Method to view sent mails.
     */
async sentMail(){
       const root = this.root.el
       root.querySelector('.sent')?.classList.add('active');
       root.querySelector('.archieved-mail')?.classList.remove('active');
       root.querySelector('.sent-mail')?.classList.remove('active');
       root.querySelector('.outbox')?.classList.remove('active');
       root.querySelector('.all_mail')?.classList.remove('active');
       root.querySelector('.inbox')?.classList.remove('active');
       root.querySelector('.done')?.classList.remove('active');
       this.mailState.mailType = "sent"
        if (this.mailState.currMailType != 'sentMail'){
            this.mailState.prevMailType = this.mailState.currMailType
       }
        if (this.mailState.prevMailType != 'sentMail' &&  this.mailState.currMailType != 'sentMail'){
            this.mailState.offset = 0
       }
       this.mailState.currMailType = 'sentMail'
       this.resetView()
       const currentUserId = await this.orm.call('res.users', 'get_current_user_id', []);
       const domain = [
            ['is_odoo_mail_message', '=', true],
            ['is_trashed', '=', false],
            ['message_type', 'in', ['comment','email_outgoing']]
        ];
        const total = await this.orm.searchCount('mail.message', domain);
        this.mailState.totalRecords = total;
        const records = await this.orm.call(
            'mail.message', 'search_read',
            [domain, []],
            { limit: this.mailState.limit,
              offset: this.mailState.offset,
              order: "create_date desc" }
        );
        this.mailState.loadMail = records;
        this.mailState.allRecordsLoaded = this.mailState.offset + this.mailState.limit >= this.mailState.totalRecords;
        this.addPaginationControls();
        this.clearSelections();
}
//    this.mailState.loadMail = await this.orm.searchRead('mail.mail',[['state', '=', 'sent'], ['is_trashed', '=', false],
//     ['create_uid', '=', currentUserId]], [], { order: "create_date desc" });

//    this.mailState.loadMail = await this.orm.searchRead('mail.mail',[['state', '=', 'sent'], ['is_trashed', '=', false]],[], { order: "create_date desc"})
//    this.mailState.loadMail = await this.orm.searchRead('mail.mail',[['create_uid', '=', this.env.uid],['state', '=', 'sent'],['is_trashed', '=', false]], [], { order: "create_date desc" });
//    this.mailState.loadMail = await this.orm.searchRead('mail.mail',[['create_uid', '=', session.uid],['state', '=', 'sent']],[], { order: "create_date desc"})
    /**
     * Method to redirect to the calendar view.
     */
     redirectCalender(){
     this.action.doAction({
                name: "Calender",
                type: 'ir.actions.act_window',
                res_model: 'calendar.event',
                view_mode: 'calendar,list',
                view_type: 'calendar',
                views: [[false, 'calendar'], [false, 'list']],
                target: 'current',
            });
    }
     /**
     * Method to redirect to the contacts view.
     */
    redirectContacts(){
    this.action.doAction({
                name: "Contacts",
                type: 'ir.actions.act_window',
                res_model: 'res.partner',
                view_mode: 'kanban,form,list,activity',
                view_type: 'kanban',
                views: [[false, 'kanban'], [false, 'form'], [false, 'list'], [false, 'activity']],
                target: 'current',
            });
    }
    /**
     * Method to search mails based on user input.
     */
    searchMail(){
      var value= this.root.el.querySelector(".header-search-input").value.toLowerCase()
      var inboxItems = this.root.el.querySelectorAll(".inbox-message-item");
      inboxItems.forEach(item => {
      var itemText = item.textContent.toLowerCase();
      item.style.display = itemText.includes(value) ? "" : "none";
    })
    }
}
odooMail.template = 'OdooMail'
odooMail.components = {
    MailBody, SentMail, ComposeMail,MessageView,ImportDialog
}
registry.category('actions').add('odoo_mail', odooMail);
