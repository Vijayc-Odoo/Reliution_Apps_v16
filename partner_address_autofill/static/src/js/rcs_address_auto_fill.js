/** @odoo-module **/

import { Component,useState,onWillUnmount,onWillDestroy,onMounted,onWillStart,onChange} from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { CharField, charField } from "@web/views/fields/char/char_field";

const fieldRegistry=registry.category("fields");
export class RcsAddressAutoFill extends CharField {
    static template = "partner_address_autofill.RcsAddressAutoFill";
    static props = {
        ...CharField.props,
    };

    setup() {
        this.address = [];
        this.state = useState({
            query: "",
            results: [],
        });

        onMounted(() => {
//          Get the element where the user click
            document.addEventListener("click", this._onDocumentClick);
        });

        onWillUnmount(() => {
            document.removeEventListener("click", this._onDocumentClick);
        });

        onWillStart(() => {
            this.state.query = " "
        });
    }

    _onInput(ev) {
        const value = ev.target.value;
        this.state.query = value;
        if (document.querySelector('#rcs_dropdown_item')) {
            document.querySelector('#rcs_dropdown_item').remove()
        }
//        Search the place then the user enter the text in input field
        this._searchPlace(value);

    }

    _onDocumentClick = (ev) => {
//      Clear the input and dropdown values when the user clicks anywhere outside the input field or dropdown.
        if (!ev.target.parentElement.classList.contains("rcs_js_cls_addresses_dropdown") && !ev.target.parentElement.classList.contains("rcs_partner_custom_class")) {
            console.log("DocumentClick Method Call: " + ev.target.parentElement.className);
            if(document.querySelector('#enterLocation')){
                document.querySelectorAll('#enterLocation').forEach(el => {
                    el.value = "";
                });
            }
            if (document.querySelector('#rcs_dropdown_item')) {
                document.querySelector('#rcs_dropdown_item').remove()
            }
        }
    }

    async _selectItem(ev) {
        ev.currentTarget.dataset.placeId
        const name = ev.currentTarget.dataset.placeName
        const detailAddress = await rpc("/rcs_detail_gmap/address", {
            address: ev.currentTarget.dataset.placeId,
            place_id: ev.currentTarget.dataset.placeId,
            resModel: this.props.record.resModel,
            widget_field_name: this.props.name,
        })
        this.state.results = [];
        const nm=this.props.name;
        if(document.querySelector('#enterLocation')){
            document.querySelectorAll('#enterLocation').forEach(el => {
                el.value = "";
            });
        }
        detailAddress[nm]=name;

//        Set the address value when the user selects an address.
        await this.props.record.update(detailAddress);
    }

    async _searchPlace(value,resModel) {
//    Search the address based on the user's input in the field.
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