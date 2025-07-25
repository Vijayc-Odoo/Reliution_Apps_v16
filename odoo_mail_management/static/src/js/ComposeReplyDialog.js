/** @odoo-module **/
import { Component, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import {ImportDialog} from "./AttachmentMail";


export class ComposeReplyDialog extends Component {
    setup() {
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.action = useService("action");

        debugger;
        this.state = useState({
//            recipient: this.props.mail.email_from,
            recipient: this.props.mail.email_to,
            subject: `Re: ${this.props.mail.subject}`,
            content: "",
            attachedFiles: [],
            images: [],
//            cc: this.props.mail.email_cc || "",
            cc: "",
        });

        this.fileInputRef = useRef('fileInput');
        this.recipientInputRef = useRef('recipientInput');
        this.ccInputRef = useRef('ccInput');
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

    async sendReply() {
        debugger;
        const { recipient, subject, content, images, cc} = this.state;
        if (!content) {
            alert("Please enter a message");
            return;
        }
        // Prepare attachments data
        const attachments = this.state.attachedFiles.map(file => {
            if (file instanceof File) {
                return {
                    name: file.name,
                    datas: this.state.images.find(img => img.name === file.name)?.image_uri || '',
                    mimetype: file.type
                };
            }
            return file;
        });
        await this.orm.call('mail.mail', 'reply_mail', [this.props.mail.id],
         { reply_content: content,
         attachments: attachments,
         cc: cc,
         });
        this.props.close();
        window.location.reload();
    }

    async attachmentAction() {
        debugger;
        this.dialog.add(ImportDialog, {
            addAttachment: this.addAttachment.bind(this)
        })
    }

    async imageReader(file) {
        debugger;
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
        debugger;
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

    closePopup() {
        this.props.close();
    }
}

ComposeReplyDialog.template = 'ComposeReplyDialog';
ComposeReplyDialog.components = { Dialog };
