
$(document).ready(function () {
    $.ajax({
        type: "GET",
        url: '/api/conference-applications/',
        success: function(data) {
            var $ul = $('.conf-list');
            for(var i = 0; i < data.length; i++) {
                var name = data[i].name;
                var $li = $('<li>');
                $li.append($('<span>', {
                    text: name
                }));
                var keywords = data[i].keywords;
                var keywords_values = [];
                for(var j = 0; j < keywords.length; j++) {
                    var keyword_name = keywords[j].name;
                    var keyword_style = '';
                    if (keywords[j].tag) {
                        keyword_style = 'style="color: blue;"';
                    }
                    var keywords_value = "<a " + keyword_style +
                        " href='/debug/conf_app/by_keyword/" + keyword_name +
                        "'>" + keyword_name + "</a>";
                    keywords_values.push(keywords_value);
                }
                if (keywords_values.length) {
                    $li.append($('<span>', {
                        html: ' (' + keywords_values.join(', ') + ')'
                    }));
                }
                $ul.append($li);
            }
        }
    });
});
