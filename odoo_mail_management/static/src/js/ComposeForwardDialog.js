/** @odoo-module **/

import { Component, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { ImportDialog } from "./AttachmentMail";

export class ComposeForwardDialog extends Component {
    setup() {
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.action = useService("action");
        this.notification = useService("notification");

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
            recipient: "",
            subject: `Fwd: ${this.props.mail.main_subject || this.props.mail.subject}`,
            content: "",
            cc:"",
            attachedFiles: [],
            images: [],
            existingAttachments: this.props.mail.attachment_ids || [],
        });
         this.fileInputRef = useRef('fileInput');
//         this.recipientInputRef = useRef('recipientInput');
         this.ccInputRef = useRef('ccInput');
    }

    closeInput(index){
        const removedFile = this.state.attachedFiles[index];
        const updatedAttachments = [...this.state.attachedFiles];
        updatedAttachments.splice(index, 1);
        this.state.attachedFiles = updatedAttachments;
        this.state.images = this.state.images.filter(img => img.name !== removedFile.name);
    }

    async sendForward() {
        const { recipient, content, existingAttachments, cc} = this.state;
        if (!recipient || !content) {
            alert("Please enter recipient and message");
            return;
        }

        try {
            const newAttachments = this.state.attachedFiles.map(file => {
                if (file instanceof File) {
                    return {
                        name: file.name,
                        datas: this.state.images.find(img => img.name === file.name)?.image_uri || '',
                        mimetype: file.type
                    };
                }
                return file;
            });
            const allAttachmentIds = [...existingAttachments].map(att => {
                if (typeof att === 'number') return att;
                return att?.id;
            }).filter(Boolean);

            console.log("Final attachment IDs:", allAttachmentIds);

            await this.orm.call('mail.mail', 'forward_mail', [this.props.mail.id], {
                forward_recipient: recipient,
                forward_content: content,
                attachment_ids: allAttachmentIds,
                new_attachment_ids: newAttachments,
                cc: cc
            });
            this.props.close();
            window.location.reload();
        }  catch (error) {
            this.notification.add("Error forwarding email: " + error, { type: 'danger' });
        }
    }

    async attachmentAction() {
        this.dialog.add(ImportDialog, {
            addAttachment: this.addAttachment.bind(this)
        });
    }

    async imageReader(file) {
        const fileReader = new FileReader();
        fileReader.onload = (event) => {
            const imageDataUrl = event.target.result;
            if (imageDataUrl) {
                this.state.images.push({ name: file.name, image_uri: imageDataUrl.split(",")[1] });
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

    addAttachment(attachment) {
        this.state.attachedFiles.push(attachment);

        if (attachment instanceof File) {
            this.contentHandler(attachment);
        } else if (attachment.data && attachment.mimetype) {
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

    closePopup() {
        this.props.close();
    }
}

ComposeForwardDialog.template = 'ComposeForwardDialog';
ComposeForwardDialog.components = { Dialog };


