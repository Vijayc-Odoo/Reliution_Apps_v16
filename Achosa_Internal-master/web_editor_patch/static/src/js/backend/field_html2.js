odoo.define('web_editor_patch.field.html', function (require) {
  'use strict';
    
    var field_registry = require('web.field_registry');
    require('web._field_registry');
    require('web_editor.field.html');

    const { patch } = require('web.utils');
    const FieldHtml = require('web_editor.field.html');

    FieldHtml.include({
        _onChange: function (ev) {
            this._doDebouncedAction.apply(this, arguments);
            // AO-985: fix Email editor freezing page and not working
            if(!this.$content){
                return;
            }
          return this._super.apply(this, arguments);
        },
    });
});