odoo.define('sh_contact_address_google_place.ShAddressAutoComplete', function (require) {
    'use strict';

    var basic_fields = require('web.basic_fields');
    var core = require('web.core');
    var fieldRegistry = require('web.field_registry');
    var QWeb = core.qweb;

    var FieldChar = basic_fields.FieldChar;
    var ShAddressAutoComplete = FieldChar.extend({
        /**
         * To Remove Dropdown from viewport.
         * @private
         * @param {object} container
         */
        _removeAddressesDropdown(container) {
            if (container !== undefined) {
                const addressDropdown = container.find('.sh_js_cls_addresses_dropdown');
                if (addressDropdown) {
                    addressDropdown.remove();
                }
            }
        },
        /**
         * @private
         * @param {string} value - searched term
         */
        _suggestAddresses: async function (value) {
            if (value) {
                const inputC = this.$el.parent();
                this._removeAddressesDropdown(inputC);
                const addresses = await this._rpc({
                    route: "/sh_find_on_gmap/address", params: { partial_address: value }
                });
                if (addresses.length) {
                    var data = QWeb.render("sh_contact_address_google_place.AddressDropDown", {
                        addresses: addresses
                    })
                    if (data && $(data).length && inputC) {
                        var $addressDropdown = $(data)[0];
                        inputC.append($addressDropdown);
                        const addressDropdownItem = inputC.find('.sh_js_cls_addresses_dropdown > .sh_js_cls_address_dropdown_item');
                        if (addressDropdownItem.length) {
                            addressDropdownItem.on('click', this._onClickDropdownItem.bind(this))
                        }
                    }
                }
            }
        },
        /**
         * For rpc request to find google map address through _suggestAddresses method.
         * @override
         * @private
         */
        _onInput: function () {
            this._super();
            this._suggestAddresses(this.$input.val());
        },
        /**
         * This method user for handling google map address dropdown item click
         * @param {Event} ev - addresses dropdown item click event
         */
        _onClickDropdownItem: async function (ev) {
            this.$el.val(ev.currentTarget.textContent.trim());
            const inputC = this.$el.parent();
            debugger;
            const address = await this._rpc({ route: "/sh_find_on_gmap/fill_address", params: { address: this.$el.val(), place_id: ev.currentTarget.dataset.placeId } });
            this._removeAddressesDropdown(inputC);
            if (address) {
                // Write the address to the related Contact.
                this.trigger_up('field_changed', {
                    dataPointID: this.dataPointID,
                    changes: {
                        street: address.formatted_street !== undefined ? address.formatted_street : "",
                        city: address.city !== undefined ? address.city : "",
                        state_id: { id: address.state !== undefined ? address.state : false },
                        zip: address.zip !== undefined ? address.zip : "",
                        country_code: address.country_code !== undefined ? address.country_code : "",
                        country_id: { id: address.country !== undefined ? address.country : false },
                    },
                });
            }
        }

    });
    fieldRegistry.add('sh_address_auto_complete', ShAddressAutoComplete);
});