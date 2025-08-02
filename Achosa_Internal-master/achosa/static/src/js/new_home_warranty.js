               function seller_buyer_click(t){
                    if($("input[name='covered_sellers_coverage']").is(':checked') && t != 'B'){
                        $('.seller').show();
                        $('.buyer').hide();
                        $("input[name='covered_buyers_coverage']").prop( "checked", false );
                        $("input[name='covered_seller_product']").attr("required", true);
                        $("input[name='covered_buyer_product']").removeAttr("required");
                        $("input[name='covered_buyer_product']").prop( "checked", false );
                        $(".buyer checkbox").prop( "checked", false );
                        $("input[name='seller_name']").attr("required", true);
                        $("input[name='buyer_name']").removeAttr("required");
                        $("input[name='covered_buyers_coverage']").removeAttr("required");
                    }else if($("input[name='covered_buyers_coverage']").is(':checked')){
                        $('.buyer').show();
                        $('.seller').hide();
                        $("input[name='covered_sellers_coverage']").prop( "checked", false );
                        $("input[name='covered_seller_product']").removeAttr("required");
                        $("input[name='covered_seller_product']").prop( "checked", false );
                        $("input[name='covered_buyer_product']").attr("required", true);
                        $("input[name='buyer_name']").attr("required", true);
                        $("input[name='seller_name']").removeAttr("required");
                        $("input[name='covered_sellers_coverage']").removeAttr("required");
                    }else{
                        $('.buyer').hide();
                        $('.seller').hide();
                        $("input[name='covered_sellers_coverage']").removeAttr("readonly");
                        $("input[name='covered_buyers_coverage']").removeAttr("readonly");
                        $("input[name='covered_seller_product']").removeAttr("required");
                        $("input[name='covered_buyer_product']").removeAttr("required");
                        $("input[name='buyer_name']").removeAttr("required");
                        $("input[name='seller_name']").removeAttr("required");
                        $("input[name='covered_sellers_coverage']").attr("required", true);
                        $("input[name='covered_buyers_coverage']").attr("required", true);
                    }
                    chg_states();
                }
                function re_calc(){
                    var myform = $( "#website_form" );
                    var disabled = myform.find(':input:disabled').removeAttr('disabled');
                    var formData = myform.serializeArray();
                    console.log("SerializeArray -> Form Data -> ", formData);
//                    var rentalAddonId = 190;
                    var rentalAddonId = parseInt($("#non_owner_product_add_on_id").val());
                    console.log("Method: re_calc, Rental Addon Id: ", rentalAddonId);
                    
                    var alreadyChecked = "False";
                    for (var i = formData.length - 1; i >= 0; --i) {
                        if (formData[i].name == 'covered_buyer_addons[]') {
                            if (formData[i].value == rentalAddonId) {
                                alreadyChecked = "True";
                            }
                        }
                    }
                    if(alreadyChecked == "False"){
                        $('#rental_property').val('False');
                    } else {
                        $('#rental_property').val('True');
                    }
                    var property_type = $("#property_type").val();

                    if((property_type == 'Single Family Home') || (property_type == 'Townhome/Condo') || (property_type == 'New')){
                        $('.rental').show();
                        $(`#${rentalAddonId}_addon`).show();

                    } else {
                        $('.rental').hide();
                        $('#rental_property').val('False');
                        if (alreadyChecked == "True") {
                            for (var i = formData.length - 1; i >= 0; --i) {
                                if (formData[i].name == 'covered_buyer_addons[]') {
                                    if (formData[i].value == rentalAddonId) {
                                        formData.splice(i,1);
                                    }
                                }
                            }
                        }

                        $(`#${rentalAddonId}_addon`).hide();
                        for (var i = formData.length - 1; i >= 0; --i) {
                            if (formData[i].name == 'covered_buyer_addons[]') {
                                if (formData[i].value == rentalAddonId) {
                                    formData.splice(i,1);
                                }
                             }
                        }

                    }
                    
                    
                    var conserveID = parseInt($("#conserve_add_on_id").val());
                    var conservePlusID = parseInt($("#conserve_plus_add_on_id").val());
                    console.log("Conserve ID: ", conserveID);
                    console.log("Conserve Plus ID: ", conservePlusID);
                    var conserveChecked = "False";
                    var conservePlusChecked = "False";
                    for (var i = formData.length - 1; i >= 0; --i) {
                        if (formData[i].name == 'covered_buyer_addons[]') {
                            if (formData[i].value == conserveID) {
                                conserveChecked = "True";
                            }
                        }
                    }
                    for (var i = formData.length - 1; i >= 0; --i) {
                        if (formData[i].name == 'covered_buyer_addons[]') {
                            if (formData[i].value == conservePlusID) {
                                conservePlusChecked = "True";
                            }
                        }
                    }
                    if(conserveChecked == "True"){
                        console.log("Conserve Checked");
                        $(`#${conservePlusID}_addon`).hide();
                        for (var i = formData.length - 1; i >= 0; --i) {
                            if (formData[i].name == 'covered_buyer_addons[]') {
                                if (formData[i].value == conservePlusID) {
                                    formData.splice(i,1);
                                }
                             }
                        }
                    } else {
                        console.log("Conserve Not Checked");
                        $(`#${conservePlusID}_addon`).show();
                    }
                    
                    if(conservePlusChecked == "True"){
                        console.log("Conserve Plus Checked");
                        $(`#${conserveID}_addon`).hide();
                        for (var i = formData.length - 1; i >= 0; --i) {
                            if (formData[i].name == 'covered_buyer_addons[]') {
                                if (formData[i].value == conserveID) {
                                    formData.splice(i,1);
                                }
                             }
                        }
                    } else {
                        console.log("Conserve Plus Not Checked");
                        $(`#${conserveID}_addon`).show();
                    }
                    

                    console.log(formData);
                    var serialized = {};
                    $.each(formData, function (index, fieldData) {
                        if (fieldData.name == 'covered_buyer_addons[]') {
                            let name = fieldData.name.substring(0, fieldData.name.length - 2);
                            if (!(name in serialized)) {
                                serialized[name] = [];
                            }
                            serialized['covered_buyer_addons'].push(fieldData.value);
                        } else if(fieldData.name != 'covered_buyer_addons') {
                            serialized[fieldData.name] = fieldData.value;
                        }
                    });
                    if('covered_buyer_addons' in serialized){
                        $('#covered_buyer_addons').val(serialized['covered_buyer_addons'].toString());
                        serialized['covered_buyer_addons'] = serialized['covered_buyer_addons'].toString();
                    } else {
                        $('#covered_buyer_addons').val("");
                    }
                    disabled.attr('disabled','disabled');
                    $.post("/my/home_warranties/products",serialized,
                        function( data ) { $("#products").html(data); }
                        );

                    var rentalAddon = "false";
                    var addons = myform.find("input[name='covered_buyer_addons[]']");
                    for (var i = addons.length - 1; i >= 0; --i) {
                        if ($(addons[i]).val() == rentalAddonId) {
                            rentalAddon = "true";
                        }
                    }
                    if (rentalAddon == "false") {
                        $('.rental').hide();
                    }
                    else {
                        $('.rental').show();
                    }
                    if(property_type == 'New'){
                        $("#covered_buyer_term").hide().attr('disabled','disabled');
                        $(".covered_buyer_term").show();
                    } else {
                        $("#covered_buyer_term").show().removeAttr('disabled');
                        $(".covered_buyer_term").hide()
                    }
                    var promo_code = $("#promo_code").val();
                    var btn = $("#submit_btn")
                    if(promo_code == ''){
                        btn.html("Submit Order");
                        btn.removeClass("btn-primary").addClass("btn-epsilon");
                    } else {
                        $("#submit_btn").html("Validate Promo");
                        btn.removeClass("btn-epsilon").addClass("btn-primary");
                    }
                    if ($('#status').text() == "Buyer Order Complete" || $('#status').text() == "Owner Order Complete") {
                        var rentalAddon = "false";
                        var addons = myform.find("input[name='covered_buyer_addons[]']");
                        for (var i = addons.length - 1; i >= 0; --i) {
                            $(addons[i]).attr("disabled", "disabled");
                            $(addons[i]).attr("readonly", "readonly");
                            if ($(addons[i]).val() == rentalAddonId) {
                                rentalAddon = "true";
                            }
                        }
                        if (rentalAddon == "false") {
                            $('.rental').hide();  
                        }
                        else {
                            $('.rental').show();
                        }
                        $('#rental_property').attr("disabled","disabled");
                        $('#covered_buyer_term').attr("disabled","disabled");
                    }
                    else if ($('#status').text() == "Seller Order Complete") {
                        var rentalAddon = "false";
                        var addons = myform.find("input[name='covered_buyer_addons[]']");
                        for (var i = addons.length - 1; i >= 0; --i) {
                            if ($(addons[i]).val() == rentalAddonId) {
                                rentalAddon = "true";
                            }
                        }
                        if (rentalAddon == "false") {
                            $('.rental').hide();  
                        }
                        else {
                            $('.rental').show();
                        }
                    }
                }
                function chg_states(){
                    var myform = $( "#website_form" );
                    var disabled = myform.find(':input:disabled').removeAttr('disabled');
                    var serialized = myform.serialize();
                    disabled.attr('disabled','disabled');
                    var rentalAddonId = parseInt($("#non_owner_product_add_on_id").val());
                    console.log("Method: chg_states, Rental Addon Id: ", rentalAddonId);
                    $.post("/my/home_warranties/seller_dropdown",serialized,
                        function( data ) { $("#div_covered_seller_product_id").html(data); }
                    );
                    $.post("/my/home_warranties/buyer_dropdown",serialized,
                        function( data ) { $("#div_covered_buyer_product_id").html(data); }
                    );
                    $.post("/my/home_warranties/addons",serialized,
                        function( data ) { 
                            $(".buyer-addons").html(data);
                            re_calc(); 
                            console.log($(data).find(`#${rentalAddonId}`).length);
                            if ($(data).find(`#${rentalAddonId}`).length == 0) {
                                $('.rental').hide();
                                $('#rental_property').val('False');
                            }
                            else {
                                $('.rental').show();
                            }
                        }
                    );
                }
                function valid_email(){
                    var mailformat = /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/;
                    var seller_email = $("#seller_email").val();
                    var buyer_email = $("#buyer_email").val();
                    var closing_email = $("#closing_email").val();
                    if(seller_email.length > 0 && !seller_email.match(mailformat)){
                        alert('Invalid Seller Email');
                    }
                    if(buyer_email.length > 0 && !buyer_email.match(mailformat)){
                        alert('Invalid Buyer Email');
                    }
                    if(closing_email.length > 0 && !closing_email.match(mailformat)){
                        alert('Invalid Closing Email');
                    }
                }
                function re_calc_rental(){
                    var myform = $( "#website_form" );
                    var formData = myform.serializeArray();
//                    var rentalAddonId = 190;
                    var rentalAddonId = parseInt($("#non_owner_product_add_on_id").val());
                    console.log("Method: re_calc_rental, Rental Addon Id: ", rentalAddonId);
                    var rental_property = $("#rental_property").val();

                    if(rental_property == 'True'){
                        formData.push({ name: "covered_buyer_addons[]", value: rentalAddonId });
                    } else {
                        for (var i = formData.length - 1; i >= 0; --i) {
                            if (formData[i].name == 'covered_buyer_addons[]') {
                                if (formData[i].value == rentalAddonId) {
                                    formData.splice(i,1);
                                }
                            }
                        }
                    }
                    console.log(formData);
                    var serialized = {};
                    $.each(formData, function (index, fieldData) {
                        if (fieldData.name == 'covered_buyer_addons[]') {
                            let name = fieldData.name.substring(0, fieldData.name.length - 2);
                            if (!(name in serialized)) {
                                serialized[name] = [];
                            }
                            serialized['covered_buyer_addons'].push(fieldData.value);
                        } else if(fieldData.name != 'covered_buyer_addons') {
                            serialized[fieldData.name] = fieldData.value;
                        }
                    });
                    if('covered_buyer_addons' in serialized){
                        $('#covered_buyer_addons').val(serialized['covered_buyer_addons'].toString());
                        serialized['covered_buyer_addons'] = serialized['covered_buyer_addons'].toString();
                    } else {
                        $('#covered_buyer_addons').val("");
                    }
                    $.post("/my/home_warranties/addons",serialized,
                        function( data ) { 
                            $(".buyer-addons").html(data);
                            re_calc(); 
                            console.log($(data).find(`#${rentalAddonId}`).length);
                            if ($(data).find(`#${rentalAddonId}`).length == 0) {
                                $('.rental').hide();
                                $('#rental_property').val('False');
                            }
                            else {
                                $('.rental').show();
                            }
                        }
                    );
                }
