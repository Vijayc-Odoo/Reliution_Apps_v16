            if(!$("input[name='covered_sellers_coverage']").is(':checked')){
                $('.seller').hide();
            }
            if(!$("input[name='covered_buyers_coverage']").is(':checked')){
                if(!$("input[name='covered_sellers_coverage']").is(':checked')){
                    $('.buyer').hide();
                    $("input[name='covered_sellers_coverage']").attr("required", true);
                    $("input[name='covered_buyers_coverage']").attr("required", true);
                }
            }
            function hide_submit_btn(){
                $('#submit_btn').hide();
            };
