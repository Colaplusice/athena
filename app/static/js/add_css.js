$(function () {
    $('.video-button button').addClass('btn-lg bg-primary');
    $('#snapshot').click(function (e) {
        e.preventDefault();
        alert('click!');
        $.get('/snapshot', function (data, status) {
            alert(status);
        });
        alert('finished')
    })
});
