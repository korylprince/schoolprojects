$(document).ready(function() {
    function resize() {
        // if screen is small
        if(Modernizr.mq('(max-width:640px)')) {
            // Convert Menu to button
            if ( $("#menu_button").length == 0 ) {
                $("#main-navigation").prepend('<span id="menu_button" >Menu</span>');
                $("#main-navigation ul").hide();
            }
            //generate select menu
            if ( $(".yearwrapper").length == 1 ) {
                $(".yearwrapper").hide();

                if ( $("#yearselector").length == 0 ) {
                    $(".yearwrapper").before('<select id="yearselector"></select>');
                    $("#yearselector").append('<option value="">Year</option>');
                    $(".yearwrapper a").each(function(){
                        $("#yearselector").append('<option value="'+$(this).attr('href')+'">'+$(this).html()+'</option>');
                    });
                }
            } 
        }
        else {
            $("#menu_button").remove();
            $("#main-navigation ul").show()

            $(".yearwrapper").show();
            $("#yearselector").remove();
        }
    }

    // Add toggle behavior to button
    $("#main-navigation").on('click','#menu_button',function (e) {
        if ($("#main-navigation ul").css("display") == "none") {
            $("#main-navigation ul").show();
        }
        else {
            $("#main-navigation ul").hide();
        }
    });

    // Add link functionality to year selector
    $("#content").on("change","#yearselector",function(e) {
        if ($(this).val() != '') {
            window.location = $(this).val();
        }
    });

    // Call on resize, use timeout to buffer
    var timerID;
    $(window).resize(function() {
        clearTimeout(timerID);
        id = setTimeout(resize, 10);
    });
    resize();

    if ($(".reviews").length == 1 && $(".reviews").children().length > 2) {
        $(".reviews").children().slice(2).hide();
        $(".reviews").after('<a id="showreviews">Click to show all Reviews...</a>');
    }
    $("#content").on("click","#showreviews",function(e) {
        $(".reviews").children().show();
        $("#showreviews").hide();
    });
});
