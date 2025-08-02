odoo.define('address.autocomplete.fieldchar', function (require) {
'use strict';

var FieldChar = require('web.basic_fields').FieldChar;
var rpc = require('web.rpc');
var field_registry = require('web.field_registry');

const options = {
    componentRestrictions: { country: "us" },
//    fields: ["address_components", "geometry", "icon", "name"],
    types: ["address"],
};

var FieldAutocomplete = FieldChar.extend({
    selector: '.o_address_autocomplete_property_street',
    resetOnAnyFieldChange: true,

    /**
     * @constructor
     * Prepares the basic rendering of edit mode by setting the root to be a
     * div.dropdown.open.
     * @see FieldChar.init
     */
    init: function () {
        this._super.apply(this, arguments);
        this.places_autocomplete = false;
        if (this.mode === 'edit') {
            this.tagName = 'input';
            this.className += ' dropdown open';
        }
    },

    start: function () {
        // Initialize the Google Placement API
        return this._super.apply(this, arguments).then(this._initializeGooglePlacesAPI());
    },

    /**
     * @override of FieldChar (called when the user is typing text)
     * Checks the <input/> value and shows suggestions according to
     * this value.
     *
     * @private
     */
//    _onInput: function () {
//        this._super.apply(this, arguments);
//        // Initialize the Google Placement API
//        this._initializeGooglePlacesAPI();
//    },

    /**
     * Initialize the Google Placement API
     *
     * @private
     */
    async _initializeGooglePlacesAPI() {
        var self = this;
        var g_places_autocomplete_api_key = await self._rpc({
            model: 'ir.config_parameter',
            method: 'get_param',
            args: ['google_places_autocomplete.api_key'],
        }).then(function (value) {
            console.log(`Key: google_places_autocomplete.api_key, Value: ${value}`);
            return value;
        });
        if (g_places_autocomplete_api_key){
            setTimeout(function () {
            if (self.mode === 'edit' && self._isActive && typeof(google) === 'object' && !self.places_autocomplete) {
                self.places_autocomplete = new google.maps.places.Autocomplete(self.$el[0], options);
                // When the user selects an address from the dropdown, populate the address fields in the form.
                self.places_autocomplete.addListener("place_changed", self._GPlacesFillInAddress.bind(self));
                }
            }, 300);
        }
    },
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Check if the autocomplete should be active
     * Active :
     *  - on model home.warranty
     *
     * @returns {boolean}
     * @private
     */
    _isActive: function () {
        return this.model === 'home.warranty';
    },

    /**
     * Update all the addresses fields based on selected address from google placement API suggestions
     *
     * @private
     */
    _GPlacesFillInAddress: function() {
      var self = this;

      // Get the place details from the autocomplete object.
      const place = self.places_autocomplete.getPlace();

      let propertyStreet = document.getElementsByName('property_street')[0]
      let address1 = "";
      let postcode = "";
      let changes = {'property_street2': '', 'property_city': ''};
      let propertyCountryCode = "US";

      /*
        Get each component of the address from the place details,
        and then fill-in the corresponding field on the form.
        place.address_components are google.maps.GeocoderAddressComponent objects
        which are documented at http://goo.gle/3l5i5Mr
      */
      console.log('Type of Place: ', typeof(place));
      if (typeof(place) != 'undefined' && typeof(place.address_components) != 'undefined'){
          console.log("Place Component: ", place.address_components);
          for (const component of place.address_components) {
            const componentType = component.types[0];

            switch (componentType) {
              case "street_number": {
                address1 = `${component.long_name} ${address1}`;
                break;
              }

              case "route": {
                address1 += component.long_name;
                break;
              }

              case "neighborhood": {
                changes['property_street2'] = component.long_name;
                break;
              }

              case "postal_code": {
                postcode = `${component.long_name}${postcode}`;
                break;
              }

              case "postal_code_suffix": {
                postcode = `${postcode}-${component.long_name}`;
                break;
              }

              case "locality":
                changes['property_city'] = component.long_name;
                break;

              case "administrative_area_level_1": {
                self._fetchPropertyCountry(propertyCountryCode).then(function (ids) {
                    console.log("Country Ids: ", ids);
                    if (ids){
                        self._fetchPropertyState(component.short_name, ids[0]).then(function (result) {
                            var values = {
                                ['property_state']: result,
                            }
                            self._onUpdateWidgetFields(values);
                        });
                    }
                });
                break;
              }
            }
          }
          changes['property_zip'] = postcode;
          console.log(`Address Component Values: ${JSON.stringify(changes)}`);
          self._onUpdateWidgetFields(changes);
          self._onUpdateWidgetFields({'property_street': address1});
          /*
           After filling the form with address components from the Autocomplete
           prediction, set cursor focus on the second address line to encourage
           entry of subpremise information such as apartment, unit, or floor number.
          */
          propertyStreet.focus();
      }
    },

    /**
     * Search the country and return it.
     *
     * @private
     */
    _fetchPropertyCountry(country_code) {
        var domain = [['code', '=', country_code]];
        var def = this._rpc({
                model: 'res.country',
                method: 'search',
                args: [domain],
                limit: 1,
            });
        return def;
    },

    /**
     * Search the state based on state_code and country and return it.
     *
     * @private
     */
    _fetchPropertyState(state_code_or_name, country) {
        var def = $.Deferred();
        var domain = [['enable_home_warranty', '=', true], ['country_id', '=', country], '|', ['name', '=', state_code_or_name], ['code', '=', state_code_or_name]]
        if (country && state_code_or_name) {
            rpc.query({
                model: 'res.country.state',
                method: 'search_read',
                args: [domain, ['display_name',]],
                limit: 1,
            }).then(function (record) {
                var record = record.length === 1 ? record[0] : {};
                def.resolve(record);
            });
        } else {
            def.resolve([]);
        }
        return def;
    },

    /**
     * This method is set the values in the fields,
     * values: json object, example: {field_name: value, field_name:value, ......}
     * @private
     */
    _onUpdateWidgetFields: function (values) {
        var values = values || {};
        this.trigger_up('field_changed', {
            dataPointID: this.dataPointID,
            changes: values,
            viewType: this.viewType,
        });
    },

    /**
     * @override
     */
    destroy: function () {
        if (this.places_autocomplete && this.mode == 'readonly') {
            google.maps.event.clearInstanceListeners(this.places_autocomplete);
            // Remove all PAC container in DOM if any
            $('.pac-container').remove();
        }
        return this._super();
    }
});

field_registry.add('address_autocomplete_property_street', FieldAutocomplete);

return FieldAutocomplete;
});
