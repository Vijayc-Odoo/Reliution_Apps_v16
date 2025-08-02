/** @odoo-module **/

import publicWidget from "web.public.widget";
import "website_sale.website_sale";
import ajax from "web.ajax";
import { qweb as QWeb } from "web.core";


publicWidget.registry.WebsiteSale.include({
    /**
     * Changed property type value when switch the radio button
     */

    _onChangeCombination: async function (ev, $parent, combination) {
        this._super(...arguments);
             var $product_variant_property_type_attribute_value_name = $parent.find(".att_value:first")
            $product_variant_property_type_attribute_value_name.text(combination.product_variant_property_type_attribute_value_name)

    },
});








