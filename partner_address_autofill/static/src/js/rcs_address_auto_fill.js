/** @odoo-module **/

import { AutoComplete } from "@web/core/autocomplete/autocomplete";
import { Component,useState,onWillUnmount,onWillDestroy,onMounted,onWillStart,onChange} from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation"
import { useInputField } from "@web/views/fields/input_field_hook";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { CharField, charField } from "@web/views/fields/char/char_field";
import { renderToFragment } from "@web/core/utils/render";
import { useRef } from "@odoo/owl";
import { useBus } from "@web/core/utils/hooks";

import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";

const fieldRegistry=registry.category("fields");
export class RcsAddressAutoFill extends CharField {
    static template = "partner_address_autofill.RcsAddressAutoFill";
    static props = {
        ...CharField.props,
    };

    setup() {
        debugger;
        console.log("Hello")
        this.address = [];
        var self = this;
        //        this.dropdown = useRef("placesList");
        this.state = useState({
            query: "",
            results: [],
        });


        onMounted(() => {
            debugger;
//            document.querySelector('#enterLocation').value = "";
            document.addEventListener("click", this._onDocumentClick);
//            document.querySelector('.o_form_button_create')
            console.log("hello sir ji ");
        });

        onWillUnmount(() => {
            debugger;
            document.removeEventListener("click", this._onDocumentClick);
            console.log("onWillUnmount ");
        });

        onWillStart(() => {
            debugger;
            this.state.query = " "
            console.log("hello guys");
        });
        //        setTimeout(() => {
        //            document.addEventListener("click", (ev) => {
        //                debugger;
        //                if (!ev.target.closest(".rcs_partner_custom_class")) {
        //                    console.log("CALL SET TIME OUT");
        //                }
        //            }, { once: true });
        //        });
    }

    _onInput(ev) {
        debugger;
        //        this.state.results=[];
        const value = ev.target.value;
        this.state.query = value;
        this._searchPlace(value);
        //        this.state.results=[];
    }

    _onDocumentClick = (ev) => {
        debugger;
        if (!ev.target.parentElement.classList.contains("rcs_js_cls_addresses_dropdown") && !ev.target.parentElement.classList.contains("rcs_partner_custom_class")) {
            console.log("DocumentClick Method Call: " + ev.target.parentElement.className);
            document.querySelector('#enterLocation').value = "";

            if (document.querySelector('#rcs_dropdown_item')) {
                document.querySelector('#rcs_dropdown_item').remove()
            } else {
                console.log("Dropdown does NOT exist");
            }
            //            if(state)
        } else {
            console.log("Class is either rcs_partner_custom_class or rcs_js_cls_addresses_dropdown dropdown-menu show");
        }

    }

    async discard() {
        debugger;
        console.log("Call Discard");
        //        await this.formController.discard();
    }

    onBlur(ev) {}

    async _selectItem(ev) {
        debugger;
        ev.currentTarget.dataset.placeId
        this.name=ev.currentTarget.dataset.placeName
        const detailAddress = await rpc("/rcs_detail_gmap/address", {
            address: ev.currentTarget.dataset.placeId,
            place_id: ev.currentTarget.dataset.placeId
        })

        this.state.results = [];
        document.querySelector('#enterLocation').value = "";
        await this.props.record.update({
            'street':detailAddress.street !== undefined ? detailAddress.street : "",
            'street2':detailAddress.street2 !== undefined ? detailAddress.street2 : "",
            'city':detailAddress.city !== undefined ? detailAddress.city : "",
            'zip':detailAddress.zip !== undefined ? detailAddress.zip : "",
            'rcs_contact_google_location':this.name ,
            'state_id':[detailAddress.state !== undefined ? detailAddress.state : false] ,
            'country_id': [detailAddress.country !== undefined ? detailAddress.country : false],
        })
        debugger;
        console.log("hellozsz")
    }

    async _searchPlace(value) {
        debugger;
        this.state.results = [];
        if (value) {
            this.address = await rpc("/res_find_gmap/address", {
                partial_address: value
            });
            this.state.results = this.address;

//            if (this.state.results.length) {
//                // Dynamically render the dropdown
//                const dropdownFragment = renderToFragment("partner_address_autofill.RcsAddressDropdown", {
//                    results: this.state.results,
//                });
//
//                // Append after input
//                document.querySelector(".rcs_partner_custom_class").appendChild(dropdownFragment);
//
//                // Add event listeners manually
//                document.querySelectorAll(".rcs_js_cls_address_dropdown_item").forEach((el) => {
//                    el.addEventListener("click", (ev) => this._selectItem(ev));
//                });
//            }
        }
    }
};
export const rcsAddressAutoFill = {
    ...charField,
    component: RcsAddressAutoFill,
};
fieldRegistry.add("rcs_address_auto_complete", rcsAddressAutoFill);