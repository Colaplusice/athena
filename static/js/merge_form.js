(function ($) {
    console.log('merge form');
    'use strict';
    /*[ File Input Config ]   先拿人脸融合做试点
        ===========================================================*/

    // 修改添加照片后的标签
    function change_label() {
        let file_input_form = $('.form-input-file');
        try {
            if (file_input_form[0]) {
                // 遍历得到的所有 class 为 js-input-file的 form 对象
                file_input_form.each(function () {
                    let fileInput = $(this).find(".input-file");
                    // 遍历每一个input
                    fileInput.each(function () {
                        let input_info_id = this.id + '_info';
                        $(this).on("change", function () {
                            let fileName = $(this).val();
                            if (fileName !== "") {
                                if (fileName.substring(3, 11) === "fakepath") {
                                    fileName = fileName.substring(12);
                                }
                                $('#' + input_info_id).text(fileName);
                                // show image
                                var reader = new FileReader();
                                var image_id = this.id.replace("_", '-');
                                reader.onload = function (e) {
                                    $('#' + image_id).attr('src', e.target.result);
                                };
                                reader.readAsDataURL(this.files[0]);
                            } else {
                                $('#' + input_info_id).text("没有文件选中");
                            }
                        })
                    });
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
                        var main_merge_view = $('#main_window');
                        $.ajax({
                            type: "POST",
                            url: url,
                            data: form_data,
                            cache: false,
                            contentType: false,
                            processData: false,
                        }).done(function (message, code_obj) {
                            // 利用jquery 重写dom
                            main_merge_view.html(
                                '<div class="row">' +
                                ' <div class="col-md-8 offset-4">' +
                                '<img class="img-fluid" src="' + message + '">' +
                                '<a class="btn btn-info mt-4" href="/face_merge">重新识别 </a> '+
                                '</div>' +
                                '</div>'
                            )
                            ;
                            console.log(message);
                        }).fail(function (error, message) {
                            main_merge_view.html(
                                '<div class="row text-center">' +
                                ' <div class="col-md-8 offset-4">' +
                                '<p class="mb-4">对不起，图片中貌似没有人脸</p>' +
                                '<a class="btn btn-info mt-4 " href="/face_merge">重新识别 </a> </div> ' + '</div>'
                            );
                            console.log(message);
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