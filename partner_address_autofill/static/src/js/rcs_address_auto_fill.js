/** @odoo-module **/

//import { AutoComplete } from "@web/core/autocomplete/autocomplete";
import { Component,useState,onWillUnmount,onWillDestroy,onMounted,onWillStart,onChange} from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
//import { _t } from "@web/core/l10n/translation"
//import { useInputField } from "@web/views/fields/input_field_hook";
//import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { CharField, charField } from "@web/views/fields/char/char_field";
//import { renderToFragment } from "@web/core/utils/render";
//import { useRef } from "@odoo/owl";
//import { useBus } from "@web/core/utils/hooks";
//
//import { formView } from "@web/views/form/form_view";
//import { FormController } from "@web/views/form/form_controller";

const fieldRegistry=registry.category("fields");
export class RcsAddressAutoFill extends CharField {
    static template = "partner_address_autofill.RcsAddressAutoFill";
    static props = {
        ...CharField.props,
    };

    setup() {
        debugger;
//        this.resModel=False;
        this.address = [];
//        var self = this;
        this.state = useState({
            query: "",
            results: [],
        });


        onMounted(() => {
            document.addEventListener("click", this._onDocumentClick);
        });

        onWillUnmount(() => {
            document.removeEventListener("click", this._onDocumentClick);
        });

        onWillStart(() => {
            debugger;
            this.state.query = " "
            console.log("hello guys");
        });
    }

    _onInput(ev) {
        debugger;
        const value = ev.target.value;

        this.state.query = value;
        this._searchPlace(value);
    }

    _onDocumentClick = (ev) => {
        debugger;
        if (!ev.target.parentElement.classList.contains("rcs_js_cls_addresses_dropdown") && !ev.target.parentElement.classList.contains("rcs_partner_custom_class")) {
            console.log("DocumentClick Method Call: " + ev.target.parentElement.className);
            document.querySelectorAll('#enterLocation').value = "";
            if (document.querySelector('#rcs_dropdown_item')) {
                document.querySelector('#rcs_dropdown_item').remove()
            }
        }
    }

    //    onBlur(ev) {}

    async _selectItem(ev) {
        debugger;
        ev.currentTarget.dataset.placeId
        const name = ev.currentTarget.dataset.placeName
        const detailAddress = await rpc("/rcs_detail_gmap/address", {
            address: ev.currentTarget.dataset.placeId,
            place_id: ev.currentTarget.dataset.placeId,
            resModel: this.props.record.resModel,
            widget_field_name: this.props.name,
        })
        debugger;
        this.state.results = [];
        const nm=this.props.name;
        document.querySelectorAll('#enterLocation').value = "";
        detailAddress[nm]=name;
        await this.props.record.update(detailAddress);
//        await this.props.record.update({nm: name});
//        await this.props.record.update({
//            'street': detailAddress.street !== undefined ? detailAddress.street : "",
//            'street2': detailAddress.street2 !== undefined ? detailAddress.street2 : "",
//            'city': detailAddress.city !== undefined ? detailAddress.city : "",
//            'zip': detailAddress.zip !== undefined ? detailAddress.zip : "",
//            'rcs_contact_google_location': this.name,
//            'state_id': [detailAddress.state !== undefined ? detailAddress.state : false],
//            'country_id': [detailAddress.country !== undefined ? detailAddress.country : false],
//        })
    }

    async _searchPlace(value,resModel) {
        debugger;
        this.state.results = [];
        if (value) {
            this.address = await rpc("/res_find_gmap/address", {
                partial_address: value,
                resModel:resModel
            });
            this.state.results = this.address;
        }
    }
};
export const rcsAddressAutoFill = {
    ...charField,
    component: RcsAddressAutoFill,
};
fieldRegistry.add("rcs_address_auto_complete", rcsAddressAutoFill);