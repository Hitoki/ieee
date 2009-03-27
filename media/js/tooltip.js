
function getElemPos(elem) {
    var x = y = 0;
    
    // Get the element relative to it's offset parents
    var originalElem = elem;
    do {
        x += elem.offsetLeft;
        y += elem.offsetTop;
    } while (elem = elem.offsetParent);
    
    // Now take into account any scrolling elements (except for the page scrolling)
    elem = originalElem;
    do {
        if (elem.scrollLeft != undefined && elem.scrollTop != undefined) {
            x -= elem.scrollLeft;
            y -= elem.scrollTop;
        }
    } while((elem = elem.parentNode) && elem != document.documentElement);
    
    return {x:x, y:y};
}

var Tooltip = {
    
    div: null,
    timer: null,
    
    init: function() {
    },
    
    show: function(params) {
        //console.log("Tooltip.show()");
        this.stopHideTimer();
        
        this.options = {
            elem: null,
            content: null,
            url: null,
            arrow: 'left',
            loadBeforeShowing: false
        };
        
        /*
        console.log("params: " + params);
        for (var i in params)
            console.log("params[" + i + "]: " + params[i]);
        */
        
        this.options = $.extend(this.options, params);
        
        this.hide();
        
        var str = '<div id="tooltip">'
            + '  <img src="images/tooltip_corner_top_left.png" class="tooltip-corner-top-left"/>'
            + '  <img src="images/tooltip_corner_top_right.png" class="tooltip-corner-top-right"/>'
            + '  <img src="images/tooltip_corner_bottom_left.png" class="tooltip-corner-bottom-left"/>'
            + '  <img src="images/tooltip_corner_bottom_right.png" class="tooltip-corner-bottom-right"/>';
        
        if (this.options.arrow == 'left')
            str += '  <img src="images/tooltip_arrow_left.png" class="tooltip-arrow-left"/>';
        else if (this.options.arrow == 'right')
            str += '  <img src="images/tooltip_arrow_right.png" class="tooltip-arrow-right"/>'
        
        str += '  <div id="tooltip-content">'
            + '  </div>'
            + '</div>'
        this.div = $(str).appendTo("body");
        this.content = this.div.find('#tooltip-content');
        
        this.div.hover(
            function() {
                Tooltip.onMouseOver();
            },
            function() {
                Tooltip.onMouseOut();
            }
        );
        
        var offsetLeft = 16;
        var offsetTop = -18;
        
        var pos = getElemPos(this.options.elem);
        this.div.css('left', (pos.x + this.options.elem.offsetWidth + offsetLeft) + 'px');
        this.div.css('top', (pos.y + offsetTop) + 'px');
        
        if (this.options.content)
            this.content.html(this.options.content + "!!!");
        else if (this.options.url) {
            //console.log("Loading url " + this.options.url);
            this.content.load(this.options.url, null, function() {Tooltip.onLoadUrl();});
        }
        
        if (!this.options.loadBeforeShowing) {
            //console.log("Display.");
            this.div.css('display', 'block');
        }
        else {
            //console.log("Not displaying yet.");
        }
    },
    
    onLoadUrl: function() {
        //console.log("onLoadUrl()");
        if (this.options.loadBeforeShowing) {
            //console.log("Display.");
            this.div.css('display', 'block');
        }
    },
    
    hide: function() {
        //console.log("Tooltip.hide()");
        if (this.div) {
            this.div.remove();
            this.div = null;
        }
    },
    
    onMouseOver: function() {
        this.stopHideTimer();
    },
    
    onMouseOut: function() {
        this.startHideTimer();
    },
    
    startHideTimer: function() {
        //console.log("startHideTimer()");
        this.stopHideTimer();
        this.timer = setTimeout("Tooltip.onTimer();", 500);
    },
    
    stopHideTimer: function() {
        if (this.timer) {
            clearTimeout(this.timer);
            this.timer = null;
        }
    },
    
    onTimer: function() {
        //console.log("onTimer()");
        this.hide();
    }
    
};

$(function() {
    Tooltip.init();
    //Tooltip.show();
});

