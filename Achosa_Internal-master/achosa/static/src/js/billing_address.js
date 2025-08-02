              function update_address() {
              
                var serialized = {};
                serialized['csrf_token'] = $("#csrf_token").val();
                serialized['name'] = $("#name").val();
                serialized['street'] = $("#street").val();
                serialized['street2'] = $("#street2").val();
                serialized['city'] = $("#city").val();
                serialized['state'] = $("#state").val();
                serialized['zip'] = $("#zip").val();
                serialized['country'] = $("#country").val();
                                                    
                if (document.getElementsByClassName('quotation_id').length == 0) {
                    var quotation_id = 0;
                }
                else {
                    var quotation_id = $( ".quotation_id" ).data().quotation_id;
                }
                
                $.post("/my/home_warranties/" + quotation_id + "/update_address",serialized,
                  function( data ) { console.log(data); }
                );

              }
              
              function populate_selections() {
                var serialized = {};
                console.log(document.getElementById("csrf_token"));
                serialized['csrf_token'] = document.getElementById("csrf_token").value;
                if (document.getElementsByClassName('quotation_id').length == 0) {
                    var quotation_id = 0;
                }
                else {
                    var quotation_id = $( ".quotation_id" ).data().quotation_id;
                }
                console.log(quotation_id);
                $.post("/my/home_warranties/" + quotation_id + "/retrieve_address",serialized,
                  function( data ) { $("#billing_address").html(data); }
                );
              }


              function checkPageLoad(){
                  if ( window.jQuery){
                      populate_selections();
                  }
                  else{
                      window.setTimeout("checkPageLoad();",100);
                  }
              }

              checkPageLoad();



              function check_first_last_name(name) {
                  console.log(name.value);
                  if (!name.value.includes(" ")) {
                      name.setCustomValidity('Must include both first and last name.');
                      name.reportValidity();
                  } else {
                      name.setCustomValidity('');
                      name.reportValidity();
                  }
              }
