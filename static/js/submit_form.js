(function ($) {
    console.log('enter form');
    'use strict';
    /*[ File Input Config ]
        ===========================================================*/
    // 修改添加照片后的标签
    function change_label() {
        let file_input_form = $('.form-input-file');
        try {
            if (file_input_form[0]) {
                // 遍历得到的所有 class 为 js-input-file的对象
                file_input_form.each(function () {
                    let fileInput = $(this).find(".input-file");
                    let info = $(this).find(".input-file-info");
                    fileInput.on("change", function () {
                        let fileName = $(this).val();
                        if (fileName === "") {
                            info.text("没有文件选中");
                        } else if (fileName.substring(3, 11) === "fakepath") {
                            fileName = fileName.substring(12);
                        }
                        info.text(fileName);
                    })
                });
            }
        } catch (e) {
            console.log(e);
        }
    }
    function submit_form() {
        let form = $('.form-submit-file');
        try {
            if (form[0]) {
                // 为 class=js-input-file的 form增加 submit 监听
                form.each(function () {
                    $(this).submit(function (event) {
                        event.preventDefault();
                        let url = $(this).attr('action');
                        let form_data = new FormData(this);
                        $.ajax({
                            type: "POST",
                            url: url,
                            data: form_data,
                            cache: false,
                            contentType: false,
                            processData: false,
                        }).done(function (code, message) {
                            message_view.show();
                            console.log('success');
                        }).fail(function (error, message) {
                            console.log('error');
                            alert('出错了'+message);
                            console.log(error);
                        });
                    })
                });
            }
        } catch (e) {
            console.log(e);
        }
    }
    change_label();
    submit_form();
})(jQuery);