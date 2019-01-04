$(function () {
   var keyword = $.cookie("keyword");
    if (keyword) {
         $('.input_txt').val($.cookie('keyword'));

    }

    $('.news_filter_form').submit(function () {

        $.cookie('keyword', $('.input_txt').val());
    })

})