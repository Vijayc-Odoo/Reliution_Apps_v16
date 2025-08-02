get_msg();                            
chg_states();
$("#send").on('click',function (e) {send();});
$("#send_invoice").on('click',function (e) {send_invoice();});
function seller_buyer_click(){
                if($("input[name='covered_sellers_coverage']").is(':checked') && t != 'B'){
                    $('.seller').show();
                    $('.buyer').show();
                    $("input[name='covered_buyers_coverage']").prop( "checked", false );
                    $("input[name='covered_buyer_product']").prop( "checked", false );
                    $(".buyer checkbox").prop( "checked", false );
                }else if($("input[name='covered_buyers_coverage']").is(':checked')){
                    $('.buyer').show();
                    $('.seller').hide();
                    $("input[name='covered_sellers_coverage']").prop( "checked", false );
                    $("input[name='covered_sellers_product']").prop( "checked", false );
                }else{
                    $('.buyer').hide();
                    $('.seller').hide();
                }
                chg_states();
            }
            function re_calc(){
                    var myform = $( "#website_form" );
                    var disabled = myform.find(':input:disabled').removeAttr('disabled');
                    var formData = myform.serializeArray();

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
                        if (fieldData.name != 'promo') {
                            if (fieldData.name == 'covered_buyer_addons[]') {
                                let name = fieldData.name.substring(0, fieldData.name.length - 2);
                                if (!(name in serialized)) {
                                    serialized[name] = [];
                                }
                                serialized['covered_buyer_addons'].push(fieldData.value);
                            } else if(fieldData.name != 'covered_buyer_addons') {
                                serialized[fieldData.name] = fieldData.value;
                            }
                        }
                    });
                    if('covered_buyer_addons' in serialized){
                        $('#covered_buyer_addons').val(serialized['covered_buyer_addons'].toString());
                        serialized['covered_buyer_addons'] = serialized['covered_buyer_addons'].toString();
                    } else {
                        $('#covered_buyer_addons').val("");
                    }
                    disabled.attr('disabled','disabled');
                    $.post("/my/home_warranties/"+$("#id").val()+"/products",serialized,
                        function( data ) { $("#products").html(data); }
                        );
                    
                    if(property_type == 'New'){
                        $("#covered_buyer_term").hide().attr('disabled','disabled');
                        $(".covered_buyer_term").show();
                    } else {
                        $("#covered_buyer_term").show().removeAttr('disabled');
                        $(".covered_buyer_term").hide()
                    }
                    var promo_code = $("#promo_code").val();
                    var btn = $("#submit_btn")
                    if(promo_code == ''  || $("#promo_code").attr('disabled') != undefined){
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
                var rentalAddonId = parseInt($("#non_owner_product_add_on_id").val());
                console.log("Method: chg_states, Rental Addon Id: ", rentalAddonId);
                var disabled = myform.find(':input:disabled').removeAttr('disabled');
                var serialized = myform.serialize();
                disabled.attr('disabled','disabled');
                var buyer = $("#covered_buyers_coverage").attr('checked');
                    $.post("/my/home_warranties/buyer_dropdown",serialized,
                        function( data ) { $("#div_covered_buyer_product_id").html(data); }
                    );
                    $.post("/my/home_warranties/seller_dropdown",serialized,
                        function( data ) { $("#div_covered_seller_product_id").html(data); }
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
            function get_msg(){
                console.log("TEST");
                $.get("/my/home_warranties/"+$("#id").val()+"/messages",
                    function( data ) { $("#messages").html(data); });
            }
            function send(){
                $("#send").off().addClass('disabled');
                var myform = $( "#msg_form" );
                var serialized = myform.serialize();
                myform.find("textarea").attr('disabled','disabled');
                $.post("/my/mail.mail", serialized,
                    function (result_data) {
                        result_data = $.parseJSON(result_data);
                        if (result_data.id) {
                            myform.find("#o_website_form_result").html(
"<i class='fa fa-check mr4'></i>The information has been sent successfully to customer service to update the order.");
                        } else {
                            myform.find("#o_website_form_result").html(
"<i class='fa fa-close mr4'></i> An error has occurred, the message has not been sent");
                        }
                        get_msg();
                        $("#send").on('click',function (e) {send();}).removeClass('disabled');
                        myform.find("textarea").removeAttr('disabled');
                        myform.find("textarea").val("");
                    });
            }
            function send_invoice(){
                $("#send_invoice").off().addClass('disabled');
                var template = $("#template").val();
                $.get("/my/home_warranties/"+$("#id").val()+"/send_Invoice/"+template,
                    function (result_data) {
                        $("#o_website_email_result").html(result_data);
                        $("#send_invoice").on('click',function (e) {send_invoice();}).removeClass('disabled');
                    });
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
//                var rentalAddonId = 190;
                var rentalAddonId = parseInt($("#non_owner_product_add_on_id").val());
                console.log("Method: re_calc_rental, Rental Addon Id: ", rentalAddonId);
                var rental_property = $("#rental_property").val();
                var property_type = $("#property_type").val();
                var property_state = $("#property_state").val();
                console.log(property_type);
                console.log($("#property_state"));
                formData.push({ name: "property_type", value: property_type});
                formData.push({ name: "property_state", value: property_state});
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
