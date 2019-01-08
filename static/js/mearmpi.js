$(function () {
    var tracking_cmd = ['streamonly', 'test', 'tracking'];
    var url = "";
    $('.btn').on('click', function () {
        var command = JSON.stringify({ "command": $('#' + $(this).attr('id')).val() });
        if (JSON.parse(command).command == "") {
            var command = JSON.stringify({ "command": $(this).find('input').val() });
        }
        if (tracking_cmd.includes(JSON.parse(command).command)) {
            url = '/tracking';
        }
        post(url, command);
    });
    function post(url, command) {
        $.ajax({
            type: 'POST',
            url: url,
            data: command,
            contentType: 'application/json',
            timeout: 10000
        }).done(function (data) {
            var sent_cmd = JSON.parse(command).command;
            var mearmpi_res = JSON.parse(data.ResultSet).result;
            //console.log(JSON.parse(data.ResultSet));
            $("#res").text(sent_cmd + ":" + mearmpi_res);
        }).fail(function (jqXHR, textStatus, errorThrown) {
            $("#res").text(textStatus + ":" + jqXHR.status + " " + errorThrown);
        });
        return false;
    }
    $(function () {
        $('[data-toggle="tooltip"]').tooltip()
    });
});

