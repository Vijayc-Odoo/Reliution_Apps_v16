/* @odoo-module*/
import { HtmlField, htmlField } from "@html_editor/fields/html_field";
import {Component,useState,useRef, onMounted, onWillUnmount} from '@odoo/owl'
import { useBus, useService } from "@web/core/utils/hooks";
import {ImportDialog} from "./AttachmentMail";
//import DOMPurify from 'dompurify';

/**
 * ComposeMail component for handling mail composition.
 * @extends Component
 */
export class ComposeMail extends Component {
    setup() {
        debugger;
        debugger;
        this.orm = useService('orm')
        this.root = useRef('root');
        this.action = useService('action')
        this.dialog = useService('dialog')
        this.dropdownRef = useRef("dropdown");
        this.searchInputRef = useRef("searchInput");


        if(document.querySelector('.compose-mail-container')){
            document.querySelectorAll('.compose-mail-container').forEach(el => {
                el.remove();
            });
        }
        if(document.querySelector('.compose-reply-container')){
            document.querySelectorAll('.compose-reply-container').forEach(el => {
                el.remove();
            });
        }
        if(document.querySelector('.compose-forward-container')){
            document.querySelectorAll('.compose-forward-container').forEach(el => {
                el.remove();
            });
        }

        this.state = useState({
            subject: "",
//            recipient: "",
            recipients: [],
            cc: "",
            content: "",
            images: [],
            originalHeight: null,
            minimized: false,
            attachedFiles: [],
            documentModel: false,
            documentId: false,
            documentName: "",
            availableDocuments: [],
            availableRecords: [],
            templates: [],
            loadingDocuments: false,
            loadingRecords: false,
            loadingTemplates: false,
            selectedTemplate: false,
            partnerSearchResults: [],
            currentSearchTerm: "",
            showPartnerDropdown: false,
            errors: {
                recipients: "",
                documentRecord: "",
            }
        })
        this.contentState = useState({
            images: [],
        });

//        this.validateEmail = (email) => {
//            const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
//            return re.test(String(email).toLowerCase());
//        };

        this.handleKeyDown = (ev) => {
            if (ev.key === 'Enter' && this.state.currentSearchTerm.trim()) {
                ev.preventDefault();
                this.selectPartner(this.state.currentSearchTerm);
            }
        };

        this.handleClickOutside = (ev) => {
            if (
                this.dropdownRef.el &&
                !this.dropdownRef.el.contains(ev.target) &&
                ev.target !== this.searchInputRef.el
            ) {
                this.state.showPartnerDropdown = false;
            }
        };

        onMounted(() => {
            document.addEventListener('click', this.handleClickOutside);
        });

        onWillUnmount(() => {
            document.removeEventListener('click', this.handleClickOutside);
        });

        this.loadDocumentModels();
    }

    async onDocumentRecordSelected(recordId){
        this.state.selectedTemplate = false;
        this.state.content = "";
        this.state.recipients = [];
        this.state.attachedFiles = [];
        this.state.images = [];

        if (!this.state.documentModel || !recordId) return;

        try {
            debugger;
            const numericId = typeof recordId === 'string' ? parseInt(recordId) : recordId;
            const record = await this.orm.read(
                this.state.documentModel,
                [numericId],
                ['partner_id']
            );

            if (record && record[0] && record[0].partner_id) {
                const partnerId = record[0].partner_id[0];

                const partner = await this.orm.read(
                    'res.partner',
                    [partnerId],
                    ['id', 'name', 'email']
                );

                if (partner && partner[0]) {
                    const partnerData = partner[0];
                    if (!this.state.recipients.some(r => r.id === partnerData.id)) {
                        this.state.recipients.push({
                            id: partnerData.id,
                            name: partnerData.name,
                            email: partnerData.email || ''
                        });
                    }
                }
            }
            await this.loadTemplates(this.state.documentModel, recordId);
        } catch (error) {
            console.error("Error loading document record partner:", error);
        }
    }

    async searchPartners(searchTerm) {
        this.state.currentSearchTerm = searchTerm;
        if (searchTerm.length < 1) {
            this.state.partnerSearchResults = [];
            this.state.showPartnerDropdown = false;
            return;
        }
        try {
            console.log("Searching for:", searchTerm);
            const results = await this.orm.searchRead(
                'res.partner',
                [
                    '|',
                    ['name', 'ilike', searchTerm],
                    ['email', 'ilike', searchTerm]
                ],
                ['id', 'name', 'email'],
                { limit: 10 }
            );

            this.state.partnerSearchResults = results || [];
        this.state.showPartnerDropdown = results.length > 0;
        } catch (error) {
            console.error("Error searching partners:", error);
            this.state.partnerSearchResults = [];
            this.state.showPartnerDropdown = false;
        }
    }

    async selectPartner(partnerOrEmail) {
        if (!partnerOrEmail) return;

        if (typeof partnerOrEmail === 'object' && partnerOrEmail.id) {
            if (!this.state.recipients.some(r => r.id === partnerOrEmail.id)) {
                this.state.recipients.push(partnerOrEmail);
            }
        }
        else if (typeof partnerOrEmail === 'string') {
            const email = partnerOrEmail.trim();

//            if (!this.validateEmail(email)) {
//                console.warn("Invalid email format");
//                return;
//            }

            if (this.state.recipients.some(r => r.email === email)) {
                return;
            }

            try {
                const partners = await this.orm.searchRead(
                    'res.partner',
                    [['email', '=', email]],
                    ['id', 'name', 'email'],
                    { limit: 1 }
                );

                let partner;
                if (partners.length > 0) {
                    partner = partners[0];
                } else {
                    const [createdId] = await this.orm.create('res.partner', [
                        {
                            name: email.split('@')[0],
                            email: email
                        }
                    ]);

                    const [createdPartner] = await this.orm.read(
                        'res.partner',
                        [createdId],
                        ['id', 'name', 'email']
                    );
                    partner = createdPartner;
                }

                if (partner && !this.state.recipients.some(r => r.id === partner.id)) {
                    this.state.recipients.push({
                        id: partner.id,
                        name: partner.name,
                        email: partner.email
                    });
                }
            } catch (error) {
                console.error("Error handling email recipient:", error);
            }
        }

        this.state.currentSearchTerm = "";
        this.state.partnerSearchResults = [];
        this.state.showPartnerDropdown = false;
    }

    removeRecipient(index) {
        this.state.recipients.splice(index, 1);
    }

    async imageReader(file) {
        const fileReader = new FileReader();
        fileReader.onload = (event) => {
            const imageDataUrl = event.target.result; // Data URL of the image
            if (imageDataUrl) {
                this.state.images.push({name: file.name, image_uri: imageDataUrl.split(",")[1]})
            }
        };
        fileReader.readAsDataURL(file);

    }
    contentHandler(file) {
    switch (file.type) {
        case "image/jpeg":
        case "image/png":
        case "image/gif":
        case "image/svg+xml":
        case "image/webp":
            return this.imageReader(file);
        case "application/pdf":
            return this.imageReader(file);
        case "text/csv":
            return this.csvReader(file);
        default:
            console.warn(`Unsupported file type: ${file.type}`);
    }
}

    async loadDocumentModels() {
        this.state.loadingDocuments = true;
        try {
            const models = await this.orm.call('ir.model', 'search_read', [], {fields: ['model', 'name']});
            this.state.availableDocuments = models;
        } catch (error) {
            console.error("Error loading document models:", error);
        } finally {
            this.state.loadingDocuments = false;
        }
    }

    async loadDocumentRecords(model) {
        this.state.documentId = false;
        this.state.availableRecords = [];
        this.state.selectedTemplate = false;
        this.state.templates = [];
        this.state.recipients = [];
        this.state.attachedFiles = [];
        this.state.images = [];
        this.state.content = "";

        if (!model) {
            this.state.availableRecords = [];
            this.state.documentId = false;
            return;
        }

        this.state.loadingRecords = true;
        try {
            // Only request essential fields - partner_id is assumed to exist
//            debugger;
            const records = await this.orm.call(
                model,
                'search_read',
                [],
                {
                    fields: ['id', 'display_name', 'partner_id'],
                    limit: 100
                }
            );

            this.state.availableRecords = records;
            await this.loadTemplates(model);
        } catch (error) {
            console.error("Error loading document records:", error);
            this.state.availableRecords = [];
        } finally {
            this.state.loadingRecords = false;
        }
    }

    async loadTemplates(model, recordId) {
        this.state.selectedTemplate = false;
        this.state.content = "";
        this.state.templates = [];

        if (!model || !recordId) {
            return;
        }

        this.state.loadingTemplates = true;
        try {
            const domain = [['model_id.model', '=', model]];
            const templates = await this.orm.call('mail.template', 'search_read', [domain], {fields: ['id','name', 'body_html'],});
            this.state.templates = Array.isArray(templates) ? templates : [];
             if (this.state.templates.length > 0) {
        }
        } catch (error) {

            console.error("Error loading templates for model", model, ":", error);
            this.state.templates = [];
        } finally {
            this.state.loadingTemplates = false;
        }
    }

    setTemplateContent(template) {
    if (template && template.body_html) {
        this.state.content = template.body_html;

        // Find the editable container
        const contentContainer = document.querySelector('#template-content');
        if (contentContainer) {
            // Set HTML content
            contentContainer.innerHTML = template.body_html;

            // Make it editable (redundant if already in the template)
            contentContainer.setAttribute('contenteditable', 'true');

            // Remove existing event to prevent duplicate listeners
            contentContainer.removeEventListener('input', this._onContentEdit);

            // Bind input listener to update state when edited
            this._onContentEdit = (ev) => {
                this.state.content = ev.target.innerHTML;
            };
            contentContainer.addEventListener('input', this._onContentEdit);
        }
    } else {
        console.warn("Selected template does not have a body_html field.");
    }
}


    async onTemplateChange(templateId) {
        this.state.attachedFiles = [];
        this.state.images = [];

        if (!templateId) {
            this.state.content = "";
            return;
        }
        if (!templateId && !this.state.documentId)
        return;
        this.state.loadingTemplates = true;
        try {
            const templateData = await this.orm.call( 'mail.mail','load_template',[templateId, [this.state.documentId]]);
            if (templateData) {
                this.setTemplateContent(templateData);

                // Auto-attach the returned reports
                if (templateData.attachments && templateData.attachments.length) {
                    for (const att of templateData.attachments) {
                        await this.addAttachment({
                            name: att.name,
                            data: att.datas,
                            mimetype: att.mimetype,
                        });
                    }
                }
            }
        } catch (error) {
            console.error("Error applying template:", error);
        } finally {
            this.state.loadingTemplates = false;
        }
    }

    /* Method to send the composed mail. */
    async sentMail() {

        this.state.errors = {
            recipients: "",
            documentRecord: "",
        };

        const {
            subject,
            recipients,
            cc,
            content,
            images,
            documentModel,
            documentId,
            selectedTemplate
        } = this.state

        let hasErrors = false;

//        if (recipients.length === 0) {
//            // Show error - at least one recipient required
//            console.warn("No recipients selected");
//            return;
//        }

        // Validate recipients
        if (recipients.length === 0) {
            this.state.errors.recipients = "Please add at least one recipient";
            hasErrors = true;
        }

        // Validate document selection
        if (documentModel && !documentId) {
            this.state.errors.documentRecord = "Please select a record for the chosen document type";
            hasErrors = true;
        }

        if (hasErrors) {
            return;
        }

        const recipientEmails = recipients.map(r => r.email).join(',');

        let sendMail = []
        try {
            const sendMail = await this.orm.call('mail.mail', 'sent_mail', [], {
                subject,
                recipient: recipientEmails,
                cc,
                content,
                images,
                document_model: documentModel,
                document_id: documentId,
                mail_template_id: selectedTemplate,
            });

            this.props.loadMail(...sendMail);
            this.props.close();
            window.location.reload();
        } catch (error) {
            console.error("Error sending mail:", error);
        }
    }
    /* Method to maximize or restore the mail composition window. */
//    maximizeMail() {
//        const mailBody = this.root.el;
//        const TextArea = this.root.el.querySelector("#content");
//
//        if (mailBody.classList.contains('maximized')) {
//            mailBody.style.height = '532px';
//            mailBody.style.right = '5%';
//            mailBody.style.width = '30%';
//            mailBody.style.position = 'fixed';
//            TextArea.style.height = '300px';
//        } else {
//            mailBody.style.height = '900px';
//            mailBody.style.right = '5%';
//            mailBody.style.width = '100%';
//            mailBody.style.position = 'absolute';
//
//        }
//        mailBody.classList.toggle('maximized');
//    }

    maximizeMail(ev) {
        // Prevent event bubbling
        ev.stopPropagation();
        ev.preventDefault();

        const mailBody = this.root.el;
        const TextArea = this.root.el.querySelector("#content");

        // Store current state before toggling
        const wasMaximized = mailBody.classList.contains('maximized');

        // Toggle the class first
        mailBody.classList.toggle('maximized');

        // Use requestAnimationFrame to ensure smooth transition
        requestAnimationFrame(() => {
            if (!wasMaximized) {
                // Maximizing
                mailBody.style.cssText = `
                    height: calc(100vh - 40px);
                    width: calc(100vw - 40px);
                    top: 20px;
                    left: 20px;
                    right: auto;
                    bottom: auto;
                    position: fixed;
                    border-radius: 10;
                    z-index: 1001;
                    transition: all 0.3s ease;
                    background-color: #fff;
                    display: flex; flex-direction: column;
                `;
            }
            else {
                // Restoring
                mailBody.style.cssText = `
                    position: fixed;
                    bottom: 3px;
                    right: 5%;
                    width: 35%;
                    min-width: 360px;
                    height: 70vh;
                    min-height: 400px;
                    border: 1px solid #ddd;
                    border-radius: 10px;
                    background: #fff;
                    z-index: 1000;
                    font-family: 'Segoe UI', sans-serif; box-shadow: 0px 5px 20px rgba(0,0,0,0.1);
                    transition: all 0.3s ease;
                    display: flex; flex-direction: column;
                `;
            }
        });
    }
    /**
     * Method to close the mail composition window.
     */
    Close() {
    debugger;
        this.props.close()
    }
    /**
     * Method to minimize or restore the mail composition window.
     */
    minimizeMail() {
        const mailBody = this.root.el;
        if (!this.state.minimized) {
            this.state.originalHeight = mailBody.style.height;
            mailBody.style.height = '50px';
        } else {
            mailBody.style.height = this.state.originalHeight;
        }
        this.state.minimized = !this.state.minimized;
    }
    /**
     * Method to trigger the attachment action.
     */
   async attachmentAction() {
        this.dialog.add(ImportDialog, {
            addAttachment: this.addAttachment.bind(this)
        })
    }
    closeInput(index){
        debugger;
        const removedFile = this.state.attachedFiles[index];
        // Remove from attachedFiles
        const updatedAttachments = [...this.state.attachedFiles];
        updatedAttachments.splice(index, 1);
        this.state.attachedFiles = updatedAttachments;
        // Optionally remove from images if present
        this.state.images = this.state.images.filter(img => img.name !== removedFile.name);
    }
    addAttachment(attachment) {
    debugger;
    this.state.attachedFiles.push(attachment);

    // Handle uploaded file (File object)
    if (attachment instanceof File) {
        this.contentHandler(attachment);
    }
    // Handle template-based attachment (base64 format)
    else if (attachment.data && attachment.mimetype) {
        if (attachment.mimetype.startsWith('image/') || attachment.mimetype === 'application/pdf') {
            this.state.images.push({
                name: attachment.name,
                image_uri: attachment.data,
            });
        } else {
            console.warn("Unsupported attachment type from template:", attachment.mimetype);
        }
    }
}
}
ComposeMail.template = 'ComposeMail'






