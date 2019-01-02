$(function () {

    // 关注当前新闻作者
    $(".focus").click(function () {
        var user_id = $(this).attr('data-userid')
        var params = {
            "action": "follow",
            "user_id": user_id
        }
        var a_focus = $(this)
        $.ajax({
            url: "/news/followed_user",
            type: "post",
            contentType: "application/json",
            data: JSON.stringify(params),
            success: function (resp) {
                if (resp.errno == "0") {
                    // 关注成功
                    var count = parseInt($(".follows b").html());
                    count++;
                    $(".follows b").html(count + "")
                    a_focus.hide()
                    a_focus.next().show()
                } else if (resp.errno == "4101") {
                    // 未登录，弹出登录框
                    $('.login_form_con').show();
                } else {
                    // 关注失败
                    alert(resp.errmsg)
                }
            }
        })
    })

    // 取消关注当前新闻作者
    $(".focused").click(function () {
        var user_id = $(this).attr('data-userid')
        var params = {
            "action": "unfollow",
            "user_id": user_id
        }
        var a_focused = $(this)
        $.ajax({
            url: "/news/followed_user",
            type: "post",
            contentType: "application/json",
            data: JSON.stringify(params),
            success: function (resp) {
                if (resp.errno == "0") {
                    // 取消关注成功
                    var count = parseInt($(".follows b").html());
                    count--;
                    $(".follows b").html(count + "")
                    a_focused.hide()
                    a_focused.prev().show()
                } else if (resp.errno == "4101") {
                    // 未登录，弹出登录框
                    $('.login_form_con').show();
                } else {
                    // 取消关注失败
                    alert(resp.errmsg)
                }
            }
        })
    })
})