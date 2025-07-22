/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

patch(FormController.prototype, {
    clearDropDown(){
    //  Clear input field and dropdown list data
        if(document.querySelector('#enterLocation')){
            document.querySelectorAll('#enterLocation').forEach(el => {
                el.value = "";
            });
        }
        if (document.querySelector('#rcs_dropdown_item')) {
            document.querySelector('#rcs_dropdown_item').remove()
        }
    },

    get actionMenuItems() {
        const items =super.actionMenuItems;
        //Clear the dropdown list when clicking on the form controller
        this.clearDropDown();
        return items;
    }
});