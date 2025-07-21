/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

patch(FormController.prototype, {
    clearDropDown(){
        if(document.querySelectorAll('#enterLocation')){
            document.querySelectorAll('#enterLocation').value = "";
        }

        if (document.querySelector('#rcs_dropdown_item')) {
            document.querySelector('#rcs_dropdown_item').remove()
        } else {
            console.log("Dropdown does NOT exist");
        }
        console.log("Discard Method Call");
    },

    get actionMenuItems() {
        const items =super.actionMenuItems;
        this.clearDropDown();
        return items;
    }
});