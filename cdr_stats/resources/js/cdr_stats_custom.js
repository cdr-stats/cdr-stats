var previousPoint = null;

    function showTooltip(x, y, contents) {
        $('<div id="tooltip">' + contents + '</div>').css( {
            position: 'absolute',
            display: 'none',
            top: y + 5,
            left: x + 5,
            border: '1px solid #fdd',
            padding: '2px',
            'background-color': '#fee',
            opacity: 0.80
        }).appendTo("body").fadeIn(200);
    }
    // toggle event for forms
    $(function() {

        $("#form_collapse").on('hidden.bs.collapse', function() {
            $('#toggle_btn_i_span').text(gettext('advanced search'));
            $('#toggle_btn_i').attr('class', 'glyphicon glyphicon-zoom-in');
        });

        $("#form_collapse").on('shown.bs.collapse', function() {
            $('#toggle_btn_i_span').text(gettext('hide search'));
            $('#toggle_btn_i').attr('class', 'glyphicon glyphicon-zoom-out');
        });
    });

    $(function() {
        $('.elemtooltip').tooltip('hide')
    });
    function MonthName(m, type){
        var short_month = new Array(
                gettext("jan"),
                gettext("feb"),
                gettext("mar"),
                gettext("apr"),
                gettext("may"),
                gettext("jun"),
                gettext("jul"),
                gettext("aug"),
                gettext("sep"),
                gettext("oct"),
                gettext("nov"),
                gettext("dec"),
        );
        var month = new Array(
                gettext("january"),
                gettext("february"),
                gettext("march"),
                gettext("april"),
                gettext("may"),
                gettext("june"),
                gettext("july"),
                gettext("august"),
                gettext("september"),
                gettext("october"),
                gettext("november"),
                gettext("december"),
        );
        if (type == 0)
            return short_month[m-1];
        else
            return month[m-1];
    }