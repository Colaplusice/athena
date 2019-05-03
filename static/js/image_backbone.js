var message_view=message_view||{};

$(function () {
    console.log("backbone up!");
    let ImageMessage = Backbone.Model.extend({
            defaults: {
                image: "/static/face_result.jpg",
            }
        }
    );
    let IndexView = Backbone.View.extend({
        el: "#index-view",
        template: _.template($('#image-template').html()),
        events: {
            'click #show-template': 'show',
            'change #select-image-recognize': 'show_image',
        },
        show_image: function () {
            // 监听选择图片检测
            $('#select-image-recognize').submit();
            // show();
        },

        show: function () {
            //指定子元素
            this.$el.html(this.template(this.model.toJSON()));
        },
    });
    let video_message = new ImageMessage();
     message_view = new IndexView({
        model: video_message
    });
});
