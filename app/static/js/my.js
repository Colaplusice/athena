function show_rec_btn() {
    $('#recongize-img').show();
    $('#snapshot').removeClass('d-none');
}

//
// (function poll() {
//     setTimeout(function () {
//         $.ajax({
//             url: "/server/api/function",
//             type: "GET",
//             success: function (data) {
//                 console.log("polling");
//             },
//             dataType: "json",
//             complete: poll,
//             timeout: 2000
//         })
//     }, 5000);
// })();

$(function () {
    // doPoll(progress);
    let Message = Backbone.Model.extend({
            defaults: {
                face_number: 0,
                people_name: "fjl",
            }
        }
    );
    let MessageView = Backbone.View.extend({
        el: "#message",
        template: _.template($('#videoMessage').html()),
        events: {
            'click #view-message': "show",
            'click #snap': "snap",
            'click #upload_recognition': function () {
                this.upload('/upload_recognition')
            },
            'click #ajax': 'ajasx',
            'click #progress': 'progress',
            'click #save-database': function () {
                this.upload('/save_database')
            }
        },
        progress: function () {
            $(".progress-bar").css("width", "75%").text("75%");
        },
        ajasx: function () {
            $.ajax({
                // "crossDomain": true,
                type: "POST",
                url: '/test_ajax',
                'data': JSON.stringify({"name": 'fjl', 'value': 23}),
                contentType: 'application/json; charset=utf-8',
                // "processData": false,
                success: function (msg) {
                    alert(msg);
                },
                failure: function (errMsg) {
                    alert(errMsg);
                }
            })
        },

        upload: function (url_path) {
            var Pic = document.getElementById("canvas").toDataURL("image/png");
            var people_name=document.getElementById('canvas').getAttribute('name');
            if (people_name===""){
                people_name="reco_image"
            }
            alert('采集成功! 人名:'+people_name);
            let timestamp=Date.now().toString();
            const image_name=people_name+'_'+timestamp.substring(timestamp.length-5,timestamp.length)+'.jpg';
            Pic = Pic.replace(/^data:image\/(png|jpg);base64,/, "");
            let data = Pic;
            let full_data = {
                'data': data,
                'image_name': image_name,
            };
            $.ajax({
                type: 'POST',
                url: url_path,
                data: JSON.stringify(full_data),
                contentType: 'application/json; charset=utf-8',
                dataType: 'json',
                success: function (msg) {
                    $("#RecoResult").modal('show');
                    console.log(msg);
                },
                failure: function (error) {
                    alert(error)
                }
            });
        },
        snap: function () {
            alert("cut!");
            var canvas = document.getElementById("canvas");
            var context = canvas.getContext("2d");
            var video = document.getElementById("video");
            context.drawImage(video, 0, 0, video.width*0.9, video.height*0.9);
            show_rec_btn();
        },

        show: function () {
            //指定子元素
            this.$el.children('#video_message_p').html(this.template(this.model.toJSON()))
        }
    });
    let video_message = new Message();
    let message_view = new MessageView({
        model: video_message
    });
});