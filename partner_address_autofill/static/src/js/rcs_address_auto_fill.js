/** @odoo-module **/

import { Component} from "@odoo/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation"
import { useInputField } from "@web/views/fields/input_field_hook";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

const fieldRegistry=registry.category("fields");
export class RcsAddressAutoFill extends Component {
    static template = "partner_address_autofill.RcsAddressAutoFill";
        static props = {...standardFieldProps};

    setup() {
    debugger;
    console.log("Hello")
    this.address = ["221B", "Baker Street", "London", "NW1", "UK"];
    }

};
export const rcsAddressAutoFill = {
    component: RcsAddressAutoFill,
};
fieldRegistry.add("rcs_address_auto_complete", rcsAddressAutoFill);