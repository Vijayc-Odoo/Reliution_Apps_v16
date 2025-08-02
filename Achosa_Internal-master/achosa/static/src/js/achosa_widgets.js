
odoo.define('achosa_widgets', function(require)
{
    var registry = require('web.field_registry'),
        AbstractField = require('web.AbstractField'),
        relational_fields = require('web.relational_fields');
    //var qweb = core.qweb;
    var FieldScript = AbstractField.extend({
        className: 'oe_form_field_script',
        init: function()
        {
           this._super.apply(this, arguments);
           this.user_list = {
               1: {
                   name: 'Administrator',
               },
               4: {
                   name: 'Demo user',
               },
           };
        },
        _render: function () {
            if (this.value) {
                this.$el.html("<script>function set_Prices(){\n" + this.value + "\n}\nset_Prices();</script>");
            }
        },
    });
    var FieldAddOns = relational_fields.FieldMany2ManyCheckBoxes.extend({template: 'FieldAddOns' });
    registry.add('FieldScript', FieldScript);
    registry.add('many2many_addons', FieldAddOns)

    return {
        FieldScript: FieldScript,
    }
});


odoo.define('web_confirm_on_save.web_confirm_on_save', function (require) {
  "use strict";

  var ajax = require('web.ajax');
  var AbstractView = require('web.AbstractView');
  var FormController = require('web.FormController');
  var Dialog = require('web.Dialog');
  var session = require('web.session');
  var core = require('web.core');
  var _t = core._t;

  AbstractView.include({

      init: function (viewInfo, params) {
          var self = this;
          this._super.apply(this, arguments);
          var confirm =  this.arch.attrs.confirm ? this.arch.attrs.confirm : false;
          var alert =  this.arch.attrs.alert ? this.arch.attrs.alert : false;
          self.controllerParams.activeActions.confirm = confirm;
          self.controllerParams.activeActions.alert = alert;
      },

  });

  FormController.include({

      check_condition: function (modelName, record_id ,data_changed) {
          var def = this._rpc({
              "model": modelName,
              "method": "check_condition_show_dialog",
              "args": [record_id ,data_changed]
          });
          console.log(def);
          return def;
      },

      checkCanBeSaved: function (recordID) {
          var fieldNames = this.renderer.canBeSaved(recordID || this.handle);
          if (fieldNames.length) {
              return false;
          }
          return true;
      },

      checkClaimExist: function(modelName,data){
          var def = this._rpc({
              "model": modelName,
              "method": "claim_subcription_exists",
              "args": [data]
          });
          return def;
      },

      _onSave: function (ev) {
          var self = this;
          var modelName = this.modelName ? this.modelName : false;
          var record = this.model.get(this.handle, {raw: true});
          var data_changed = record ? record.data : false;
          var record_id = data_changed && data_changed.id ? data_changed.id : false;
          var confirm = self.activeActions.confirm;
          var alert =  self.activeActions.alert;
          var canBeSaved = record && record.id ? self.checkCanBeSaved(record.id) : false;

          function saveAndExecuteAction () {
             ev.stopPropagation(); // Prevent x2m lines to be auto-saved
             self._disableButtons();
             self.saveRecord().then(self._enableButtons.bind(self)).guardedCatch(self._enableButtons.bind(self));
          }
          if(canBeSaved && modelName && (confirm || alert)){
              self.checkClaimExist(modelName,record).then(function(claimExist){
                  if(claimExist['name']){
                      self.check_condition(modelName, record_id, data_changed).then(function(opendialog){
                          if(!opendialog){
                              saveAndExecuteAction();
                          }
                          else{
                              if(confirm){
                                 var def = new Promise(function (resolve, reject) {
                                     var $content = $("<p>Are you sure you want to create another claim for this customer?<br/>Claim: "+claimExist['name']+"<br>Status: "+claimExist['status']+"<br/><a target='_blank' href='/web#id=" +claimExist['id']+ "&view_type=form&model=claims'>Click to view existing Claim</a></p>");
                                     Dialog.confirm(self,'', {
                                         confirm_callback: saveAndExecuteAction,
                                         $content: $content,
                                     }).on("closed", null, resolve);
                                 });
                              }
                              else{
                                  var def = new Promise(function (resolve, reject) {
                                      Dialog.alert(self, alert, {
                                          confirm_callback: saveAndExecuteAction,
                                      }).on("closed", null, resolve);
                                  });
                                  saveAndExecuteAction();
                              }
                          }
                      });
                  }
                  else{
                      saveAndExecuteAction();
                  }
             });
          }
          else{
              saveAndExecuteAction();
          }
      },
  });
});