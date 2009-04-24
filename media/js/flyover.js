/**
 * Flyover.js
 * Written 10/28/2008, James Yoneda.
 * 
 * The Flyover object handles tooltip-style popups.  Normally activated when user hovers over an object.  It is a singleton object that only shows one flyover at a time.
 * 
 */
 
// Flyover Object //////////////////////////////////////////////////////////////

// Returns the element's position relative to the page.
function getElemPos(elem) {
    elem = $(elem)[0];
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

var Flyover = {
    
    // Public //////////////////////////////////////////////////////////////////
    init: function() {
        $(document.body).click(function() {
            Flyover._onBodyClick();
        });
    },
    
    // Attaches a flyover to the given element, using its 'title' attribute as content.
    attach: function(elem, options) {
        elem = $(elem)[0];
        
        // TODO: when attaching to flyover elements in lightboxes, the $(elem).click() functions do not work!!!  Only the direct HTML onclick() type handlers work...
        elem.onmouseover = function() {
            Flyover.show(this, options);
        }
        elem.onmouseout = function() {
            Flyover.onMouseOut();
        }
        
        if (('showInitial' in options && options.showInitial) || ('showInitial' in $(elem).metadata() && $(elem).metadata().showInitial)) {
            Flyover.show(elem, options);
        }
        
        /*
        elem = $(elem);
        elem.hover(
            function() {
                Flyover.show(this, options);
            },
            function() {
                Flyover.onMouseOut();
            }
        );
        */
    },
    
    // Attaches a flyover to the given element, using its 'title' attribute as content.
    attachClick: function(elem, options) {
        options.event = 'click';
        elem = $(elem);
        elem.click(function() {
            Flyover.show(this, options);
        });
    },
    
    // Shows a flyover for the given element
    show: function(elem, options) {
        this._stopHideTimer();    
        
        elem = $(elem);
        
        if (!elem) {
            alert('Flyover: elem argument is required');
            return;
        }
        
        if (this._elem && this._elem[0] == elem[0]) {
            // Flyover is already showing this element
            this._stopHideTimer();
            return;
        } 
        
        // Hide any existing flyover
        this.hide(true);
        
        // The default options
        this.options = {
            position: 'right-top',
            hideDelay: 200,
            width: null,
            height: null,
            shadows: true,
            customClass: null,
            event: 'hover',
            arrow: true,
            content: null,
            sticky: false,
            closeButton: false,
            clickOffClose: false,
            showCallback: null,
            closeCallback: null,
            closeOnMouseOutLink: true,
            url: null,
            showInitial: false
        };
        this.options = $.extend(this.options, options);
        this.options = $.extend(this.options, elem.metadata());
        this._elem = elem;
        
        // Validate options
        if ($.inArray(this.options.position, ['left', 'left-top', 'left-bottom', 'right', 'right-top', 'right-bottom', 'top', 'top-left', 'top-right', 'bottom', 'bottom-left', 'bottom-right']) == -1) {
            alert('Flyover: unrecognized position "' + this.options.position + '"');
            return;
        } else if (isNaN(parseInt(this.options.hideDelay))) {
            alert('Flyover: hideDelay is not a number (' + this.options.hideDelay + ')');
            return;
        } else if (this.options.width != null && isNaN(parseInt(this.options.width))) {
            alert('Flyover: width is not a number (' + this.options.width + ')');
            return;
        } else if (this.options.height != null && isNaN(parseInt(this.options.height))) {
            alert('Flyover: height is not a number (' + this.options.height + ')');
            return;
        } else if (this.options.shadows !== true && this.options.shadows !== false) {
            alert('Flyover: shadows must be true or false (' + this.options.shadows + ')');
            return;
        } else if (this.options.customClass !== null && typeof this.options.customClass != 'string') {
            alert('Flyover: customClass must be null or a string (' + this.options.customClass + ')');
            return;
        } else if (typeof this.options.event != 'string') {
            alert('Flyover: event must be a string (' + this.options.event + ')');
            return;
        } else if (this.options.event != 'hover' && this.options.event != 'click') {
            alert('Flyover: event must be "hover" or "click" (' + this.options.event + ')');
            return;
        } else if (typeof this.options.arrow != 'boolean') {
            alert('Flyover: arrow must be a boolean (' + this.options.arrow + ')');
            return;
        } else if (this.options.content !== null && typeof this.options.content != 'string') {
            alert('Flyover: content must be null or a string (' + this.options.content + ')');
            return;
        } else if (typeof this.options.sticky != 'boolean') {
            alert('Flyover: sticky must be a boolean (' + this.options.sticky + ')');
            return;
        } else if (typeof this.options.closeButton != 'boolean') {
            alert('Flyover: closeButton must be a boolean (' + this.options.closeButton + ')');
            return;
        } else if (typeof this.options.clickOffClose != 'boolean') {
            alert('Flyover: clickOffClose must be a boolean (' + this.options.clickOffClose + ')');
            return;
        } else if (this.options.showCallback !== null && typeof this.options.showCallback != 'function') {
            alert('Flyover: showCallback must be null or a function (' + this.options.showCallback + ')');
            return;
        } else if (this.options.closeCallback !== null && typeof this.options.closeCallback != 'function') {
            alert('Flyover: closeCallback must be null or a function (' + this.options.closeCallback + ')');
            return;
        } else if (typeof this.options.closeOnMouseOutLink != 'boolean') {
            alert('Flyover: closeOnMouseOutLink must be a boolean (' + this.options.closeOnMouseOutLink + ')');
            return;
        } else if (this.options.url != null && typeof this.options.url != 'string') {
            alert('Flyover: url must be a string (' + this.options.url + ')');
            return;
        } else if (typeof this.options.showInitial != 'boolean') {
            alert('Flyover: showInitial must be a boolean (' + this.options.showInitial + ')');
            return;
        }
        
        // NOTE: Special behavior for closeOnMouseOutLink
        if (this.options.closeOnMouseOutLink && (!'hideDelay' in options && !'hideDelay' in elem.metadata())) {
            // closeOnMouseOutLink is true and there is no manually-specificied hideDelay, so shorten the default hideDelay
            this.options.hideDelay = 10;
        }
        
        // Create the flyover HTML element
        
        var customContainer = this.options.customClass ? this.options.customClass + '-flyover-container' : '';
        var customContent = this.options.customClass ? this.options.customClass + '-flyover-content' : '';
        
        // Main flyover element
        this._flyover = $('<div class="flyover-container ' + customContainer + '"></div>').appendTo('body');
        this._flyover.click(function (e) {
            e.stopPropagation();
        });
        
        // Add close button
        if (this.options.closeButton) {
            var closeButton = $('<a href="#" class="flyover-close-button"></a>').appendTo(this._flyover);
            closeButton.click(function() {
                Flyover.hide();
                return false;
            });
        }
        
        // Content element
        this.content = $('<div class="flyover-content ' + customContent + '"></div>').appendTo(this._flyover);
        
        if (!$.browser.msie && this.options.shadows) {
            // For non-IE, show drop shadows
            this.shadowBottomLeft = $('<div class="flyover-shadow-bottom-left"></div>').appendTo(this._flyover);
            this.shadowBottomMid = $('<div class="flyover-shadow-bottom-mid"></div>').appendTo(this._flyover);
            this.shadowBottomRight = $('<div class="flyover-shadow-bottom-right"></div>').appendTo(this._flyover);
            this.shadowRightTop = $('<div class="flyover-shadow-right-top"></div>').appendTo(this._flyover);
            this.shadowRightMid = $('<div class="flyover-shadow-right-mid"></div>').appendTo(this._flyover);
        }
        
        if (this.options.arrow) {
            // Add the arrow
            if (this.options.position == 'right' || this.options.position == 'right-top' || this.options.position == 'right-bottom') {
                this.arrow = $('<img src="/media/images/flyover_arrow_left.png" class="flyover-arrow"/>').appendTo(this._flyover);
            } else if (this.options.position == 'left' || this.options.position == 'left-top' || this.options.position == 'left-bottom') {
                this.arrow = $('<img src="/media/images/flyover_arrow_right.png" class="flyover-arrow"/>').appendTo(this._flyover);
            } else if (this.options.position == 'top' || this.options.position == 'top-left' || this.options.position == 'top-right') {
                this.arrow = $('<img src="/media/images/flyover_arrow_bottom.png" class="flyover-arrow"/>').appendTo(this._flyover);
            } else if (this.options.position == 'bottom' || this.options.position == 'bottom-left' || this.options.position == 'bottom-right') {
                this.arrow = $('<img src="/media/images/flyover_arrow_top.png" class="flyover-arrow"/>').appendTo(this._flyover);
            }
        }
        
        // If sticky is on, we don't need this (since the flyover will be manually closed).
        // If closeOnMouseOutLink is on, we don't want this to delay hiding the flyover.
        if (!this.options.sticky && !this.options.closeOnMouseOutLink) {
            this._flyover.hover(
                function() {
                    Flyover.onMouseOver();
                },
                function() {
                    Flyover.onMouseOut();
                }
            );
        }
        
        var content;
        
        if (this.options.url != null) {
            console.log('using URL');
            this.content.load(this.options.url, function() { Flyover._reposition(); } );
            
        } else if (this.options.content !== null) {
            // Use the given content
            this.content.html(this.options.content);
            this._reposition();
            
        } else {
            // Use the elem's title as the content
            
            // Remove title so the browser doesn't show its own tooltip
            this._elemTitle = this._elem.attr('title');
            this._elem.attr('title', '');
            
            // Parse contents
            var content = this._elemTitle;
            content = content.replace(/^([^|]+)\|/g, '<p class="flyover-heading">$1</p>');
            content = content.replace(/\|/g, '<br/>');
            
            this.content.html(content);
            this._reposition();
        }
        
        if (this.options.showCallback) 
            this.options.showCallback();
    },
    
    // Hide the flyover (either immediately, or with a fade effect)
    // Parameters:
    //     immediate - (true/*false) - if true, hides flyover immediately.  if false, starts fading out the flyover.
    // 
    hide: function(immediate) {
        this._stopHideTimer();
        if (this._flyover) {
            // NOTE: If hide() is called without immediate=true, then we're starting a fadeout.  If show() is called before the fadeout is done, then we have a racecondition (hide(), show(), then _onFadeout()).  Therefore, we use enclosures here to make sure _onFadeout() operates on the correct 'instance' of the flyover.
            var _flyover = this._flyover;
            this._flyover = null;
            var _closeCallback = this.options.closeCallback;
            this.options = {};
            
            if (this.options.url == null && this.options.content == null) {
                // Restore the title (only if not using the URL or content options)
                this._elem.attr('title', this._elemTitle);
                this._elem = null;
                this._elemTitle = null;
            }
            
            // TODO: This should be an option
            //if (immediate) {
            if (true) {
                // Remove everything now
                _flyover.remove();
                if (_closeCallback)
                    _closeCallback();
            } else {
                // Start a fadeout
                _flyover.fadeOut('fast', function() {Flyover._onFadeout(_flyover, _closeCallback);} );
            }
        }
    },
    
    onMouseOver: function() {
        this._stopHideTimer();
    },
    
    onMouseOut: function() {
        this._startHideTimer();
    },
    
    // Private /////////////////////////////////////////////////////////////////
    
    // The element
    _elem: null,
    
    // The title of the element
    _elemTitle: null,
    
    // The flyover HTML element
    _flyover: null,
    
    // A timer used for closing the flyover after a certain delay
    _timer: null,
    
    // Repositions the flyover and arrow
    _reposition: function(onLoadObject) {
        if (this._flyover) {
            var pos = getElemPos(this._elem);
            var left;
            var top;
            var arrowLeft;
            var arrowTop;
            var arrowWidth;
            var arrowHeight;
            
            if (this.options.width != null)
                this._flyover.css('width', this.options.width);
            if (this.options.height != null)
                this._flyover.css('height', this.options.height);
            
            var elemWidth = this._elem[0].offsetWidth;
            var elemHeight = this._elem[0].offsetHeight;
            var flyoverWidth = this._flyover[0].offsetWidth;
            var flyoverHeight = this._flyover[0].offsetHeight;
            
            if (this.options.arrow) {
                arrowWidth = this.arrow[0].offsetWidth;
                arrowHeight = this.arrow[0].offsetHeight;
            } else {
                arrowWidth = 0;
                arrowHeight = 0;
            }
            
            // Calculate the flyover and arrow position depending on the overall size
            if (this.options.position == 'right') {
                left = pos.x + elemWidth + arrowWidth;
                top = pos.y + elemHeight/2 - flyoverHeight/2;
                arrowLeft = -arrowWidth;
                arrowTop = -arrowHeight/2 + flyoverHeight/2 - 1;
                
            } else if (this.options.position == 'right-top') {
                left = pos.x + elemWidth + arrowWidth;
                top = pos.y + elemHeight/2 - arrowHeight/2 - 6;
                arrowLeft = -arrowWidth;
                arrowTop = 6;
                
            } else if (this.options.position == 'right-bottom') {
                left = pos.x + elemWidth + arrowWidth;
                top = pos.y + elemHeight/2 - flyoverHeight + arrowHeight/2 + 6;
                arrowLeft = -arrowWidth;
                arrowTop = flyoverHeight - arrowHeight - 6;
                
            } else if (this.options.position == 'left') {
                left = pos.x - flyoverWidth - arrowWidth + 2;
                top = pos.y + elemHeight/2 - flyoverHeight/2;
                arrowLeft = flyoverWidth - 2;
                arrowTop = -arrowHeight/2 + flyoverHeight/2 - 1;
                
            } else if (this.options.position == 'left-top') {
                left = pos.x - flyoverWidth - arrowWidth + 2;
                top = pos.y + elemHeight/2 - arrowHeight/2 - 6;
                arrowLeft = flyoverWidth - 2;
                arrowTop = 6;
                
            } else if (this.options.position == 'left-bottom') {
                left = pos.x - flyoverWidth - arrowWidth + 2;
                top = pos.y + elemHeight/2 - flyoverHeight + arrowHeight/2 + 6;
                arrowLeft = flyoverWidth - 2;
                arrowTop = flyoverHeight - arrowHeight - 6;
                
            } else if (this.options.position == 'top') {
                left = pos.x + elemWidth/2 - flyoverWidth/2;
                top = pos.y - flyoverHeight - arrowHeight;
                arrowLeft = -arrowWidth/2 + flyoverWidth/2;
                arrowTop = flyoverHeight - 2;
                
            } else if (this.options.position == 'top-left') {
                left = pos.x + elemWidth/2 - arrowWidth/2 - 6;
                top = pos.y - flyoverHeight - arrowHeight;
                arrowLeft = 6;
                arrowTop = flyoverHeight - 2;
                
            } else if (this.options.position == 'top-right') {
                left = pos.x + elemWidth/2 - flyoverWidth + arrowWidth + 6;
                top = pos.y - flyoverHeight - arrowHeight;
                arrowLeft = flyoverWidth - arrowWidth - 6;
                arrowTop = flyoverHeight - 2;
                
            } else if (this.options.position == 'bottom') {
                left = pos.x + elemWidth/2 - flyoverWidth/2;
                top = pos.y + elemHeight + arrowHeight;
                arrowLeft = -arrowWidth/2 + flyoverWidth/2;
                arrowTop = - arrowHeight;
                
            } else if (this.options.position == 'bottom-left') {
                left = pos.x + elemWidth/2 - arrowWidth/2 - 6;
                top = pos.y + elemHeight + arrowHeight;
                arrowLeft = 6;
                arrowTop = - arrowHeight;
                
            } else if (this.options.position == 'bottom-right') {
                left = pos.x + elemWidth/2 - flyoverWidth + arrowWidth + 6;
                top = pos.y + elemHeight + arrowHeight;
                arrowLeft = flyoverWidth - arrowWidth - 6;
                arrowTop = - arrowHeight;
            }
            
            // Position shadow
            if (!$.browser.msie && this.options.shadows) {
                this.shadowBottomMid.css('width', flyoverWidth - 16 + 'px');
                this.shadowRightMid.css('height', flyoverHeight - 15 + 'px');
            }
            
            left = Math.floor(left);
            top = Math.floor(top);
            arrowLeft = Math.floor(arrowLeft);
            arrowTop = Math.floor(arrowTop);
            
            this._flyover.css('left', left + 'px');
            this._flyover.css('top', top + 'px');
            
            if (this.options.arrow) {
                this.arrow.css('left', arrowLeft + 'px');
                this.arrow.css('top', arrowTop + 'px');
            }
            
            // Show the flyover
            this._flyover.css('display', 'none');
            this._flyover.css('visibility', 'visible');
            
            // TODO: This should be an option
            //this._flyover.fadeIn('normal');
            this._flyover.show();
        }
    },
    
    _onFadeout: function(_flyover, _closeCallback) {
        // Done fading out, now remove the flyover
        _flyover.remove();
        if (_closeCallback)
            _closeCallback();
    },
    
    _startHideTimer: function() {
        this._stopHideTimer();
        this._timer = setTimeout("Flyover._onTimer();", this.options.hideDelay);
    },
    
    _stopHideTimer: function() {
        if (this._timer) {
            clearTimeout(this._timer);
            this._timer = null;
        }
    },
    
    _onTimer: function() {
        this.hide();
    },
    
    _onBodyClick: function() {
        if (this._flyover) {
            if (this.options.clickOffClose) {
                this.hide();
            }
        }
    }
    
};

$(function() {
    Flyover.init();
});

// Page-specific code //////////////////////////////////////////////////////////

function attachFlyovers(elem) {
    elem = $(elem);
    elem.find('span.flyover, a.flyover').each(function() {
        Flyover.attach(this, {shadows:false});
    });
}

$(function() {
    $('span.flyover, a.flyover').each(function() {
        Flyover.attach(this, {shadows:false});
    });
    
    /*
    // Forum categories and names on the forum list page
    $('span.forum_name_outer, .forum_list dd a').each(function() {
        Flyover.attach(this, {width:150});
    });
    */
    
    // NOTE: Also in wikiword_tooltips.js
});


