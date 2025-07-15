/** @odoo-module **/

import { Component,useState} from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation"
import { useInputField } from "@web/views/fields/input_field_hook";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { CharField, charField } from "@web/views/fields/char/char_field";
import { renderToFragment } from "@web/core/utils/render";
import { useRef } from "@odoo/owl";

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
        var self=this;
//        this.dropdown = useRef("placesList");
        this.state = useState({
            query: "",
            results: [],
        });
    }

    _onInput(ev) {
        debugger;
        const value = ev.target.value;
        this.state.query = value;
        this._searchPlace(value);
    }

    onBlurInput(ev){
        console.log("hello Blur");
        document.querySelector('#enterLocation').value = "";
        this.state.results=[]
        this.state.query=""
    }

    async _selectItem(ev){
        debugger;
        document.querySelector('#enterLocation').value = "";
        ev.currentTarget.dataset.placeId
        ev.currentTarget.dataset.placeName
        const detailAddress = await rpc("/rcs_detail_gmap/address",{address: ev.currentTarget.dataset.placeId,place_id: ev.currentTarget.dataset.placeId})

//        await this.props.record.update({'street':'Vijay','street2':'chudasama','city':'Keshod','zip':362220,'country_id':{'id':104,'display_name':'India'},'country_code':'IN'})
        await this.props.record.update({
            'street':detailAddress.street,
            'street2':detailAddress.street2,
            'city':detailAddress.city,
            'zip':detailAddress.zip,
            'state_id':[detailAddress.state],
            'country_id': [detailAddress.country] ,
//            'country_code':'IN'
        })
        this.state.results=[]
    }

    async _searchPlace(value){
        debugger;
        this.state.results=[];
        if(value){
            this.address = await rpc("/res_find_gmap/address",{partial_address : value} );
            this.state.results = this.address;
        }
    }
};
export const rcsAddressAutoFill = {
    ...charField,
    component: RcsAddressAutoFill,
};
fieldRegistry.add("rcs_address_auto_complete", rcsAddressAutoFill);