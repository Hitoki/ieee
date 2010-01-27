
var Lightbox = {

    init: function() {
        this.visible = false;
        this.url = null;
        this.subscribers = {
            'clickOnLightbox': []
        }
    },

    // Clicked on a link, show the URL in the lightbox
    click: function(linkObj) {
        linkObj = $(linkObj);
        this.show(linkObj.attr('href'), linkObj.metadata());
        return false;
    },
    
    // Show the given URL in the lightbox
    show: function(url, options) {
        var lightbox = this;
        if (!this.visible) {
            
            // Options
            this.options = extendExisting(
                {
                    closeOnClickOutside: true,
                    verticalCenter: true,
                    customClass: null,
                    content: null,
                    onShowCallback: null
                },
                options
            );
            
            // Create the lightbox
            this.lightbox = $('<div id="lightbox"></div>').appendTo('body');
            this.lightboxBackground = $('<div class="lightbox-background"></div>').appendTo('body');
            
            // Create custom classes
            var customClassOuter;
            var customClassContent;
            if (this.options.customClass != null) {
                customClassOuter = this.options.customClass + '-lightbox-outer';
                customClassMiddle = this.options.customClass + '-lightbox-middle';
                customClassContent = this.options.customClass + '-lightbox-content';
            } else {
                customClassOuter = '';
                customClassMiddle = '';
                customClassContent = '';
            }
            
            if (this.options.verticalCenter) {
                this.lightboxContentOuterElem = $('<div class="vert-center-outer lightbox-content-outer ' + customClassOuter + '"></div>').appendTo(this.lightbox);
                this.lightboxContentMiddleElem = $('<div class="vert-center-middle ' + customClassMiddle + '"></div>').appendTo(this.lightboxContentOuterElem);
                this.lightboxContent = $('<div class="vert-center-inner lightbox-content ' + customClassContent + '"></div>').appendTo(this.lightboxContentMiddleElem);
            } else {
                this.lightboxContentOuterElem = $('<div class="lightbox-content-outer ' + customClassOuter + '"></div>').appendTo(this.lightbox);
                this.lightboxContent = $('<div class="lightbox-content ' + customClassContent + '"></div>').appendTo(this.lightboxContentOuterElem);
            }
            
            // Prevent the click from propagating when user clicks inside the content area
            this.lightboxContent.click(function(e) {
                //console.log('lightboxContent.click()');
                e.stopPropagation();
                lightbox._notify('clickOnLightbox');
            });
            
            // Close the lightbox if user clicks outside the content area
            $('body').click(function() {
                //console.log('body.click()');
                if (lightbox.options.closeOnClickOutside) {
                    lightbox.hide();
                }
            });
            
            this.visible = true;
            
            // Position the background
            this.updateScrollPos();
            
            // Position the lightbox
            var scrollTop = $(window).scrollTop();
            var scrollLeft = $(window).scrollLeft();
            this.lightbox.css('top', scrollTop);
            this.lightbox.css('left', scrollLeft);

        }
        
        if (this.options.content) {
            // Load the content
            this.onLoadContent(this.options.content);
        } else {
            // Load a URL
            //this.lightbox.clear();
            $.get(url, null, function(data) { lightbox.onLoadContent(data); }, 'text');
            //this.lightboxContent.load(url, null, function() { lightbox.onLoadContent(); } );
        }
    },
    
    onLoadContent: function(data) {
        var lightbox = this;
        if (this.visible) {
            
            //console.log('  data: ' + data);
            
            if (data == 'close_lightbox') {
                // Close the lightbox
                this.hide();
                
            } else if (data.substr(0, 4) == 'ajax') {
                var vars = eval("(" + data.substr(5, data.length-5) + ")");
                //for (var i in vars)
                //    console.log('vars['+i+']: ' + vars[i]);
                    
                if (window.notify != undefined) {
                    window.notify(vars.event, vars.data);
                }
                
                // TODO
                this.hide();
                
            } else {
                
                // Received plain HTML, just render
                this.lightboxContent.html(data);
                
                /*
                // Attach any multisearch objects
                if (attachMultiSearches) {
                    attachMultiSearches(this.lightboxContent);
                }
                
                // Attach any flyover objects
                if (attachFlyovers) {
                    attachFlyovers(this.lightboxContent);
                }
                
                // Attach any flyover objects
                if (attachBlurTexts) {
                    attachBlurTexts(this.lightboxContent);
                }
                */
                attachScripts(this.lightboxContent);
                
                // Hook into any forms
                var forms = this.lightboxContent.find('form');
                for (var i=0; i<forms.length; i++) {
                    var form = $(forms[i]);
                    form.submit(function(e) {
                        e.preventDefault();
                        $.post(form[0].action, form.serializeArray(), function(data){ lightbox.onFormResults(data); } );
                    });
                }
                
                // Hook into any close buttons
                this.lightboxContent.find('.lightbox-close').click(function(e) {
                    lightbox.hide();
                });
                
                if (this.options.onShowCallback) {
                    this.options.onShowCallback();
                }
            }
        }
    },
    
    onFormResults: function(data) {
        if (this.visible) {
            this.onLoadContent(data);
        }
    },
    
    hide: function() {
        if (this.visible) {
            this.lightbox.remove();
            this.lightboxBackground.remove();
            this.lightbox = null;
            this.visible = false;
        }
    },
    
    // Reposition the lightbox when user scrolls the page
    onScroll: function() {
        this.updateScrollPos();
    },
    
    updateScrollPos: function() {
        if (this.visible) {
            // Reposition the background so it's always visible.
            var scrollTop = $(window).scrollTop();
            var scrollLeft = $(window).scrollLeft();
            this.lightboxBackground.css('top', scrollTop);
            this.lightboxBackground.css('left', scrollLeft);
        }
    },
    
    // Allows another object to subscribe to this object's events.
    // @param event - the name of the event.
    // @param func - the callback function.  Will be called like:
    //   func([source_object], [event_name], [optional_event_data]);
    // 
    subscribe: function(event, func) {
        if (!event in this.subscribers) {
            alert('Lightbox.subscribe(): Unknown event "' + event + '"');
            return;
        }
        this.subscribers[event].push(func);
    },
    
    // Notify all subscribers of an event.
    _notify: function(event, data) {
        if (!event in this.subscribers) {
            alert('Lightbox.notify(): Unknown event "' + event + '"');
            return;
        }
        for (var i=0; i<this.subscribers[event].length; i++) {
            var func = this.subscribers[event][i];
            func(this, event, data);
        }
    }
}

function attachLightboxes(elem) {
    elem = $(elem);
    elem.find('.lightbox').each(function() {
        $(this).click(function(e) {
            e.preventDefault();
            Lightbox.click(this);
        });
    });
}

$(function() {
    Lightbox.init();
    
    $('.lightbox').each(function() {
        $(this).click(function(e) {
            e.preventDefault();
            Lightbox.click(this);
        });
    });
    
    $(window).scroll(function() {
        Lightbox.onScroll();
    });
    
    // DEBUG: Auto open the lightbox on page load
    //var box = $('.lightbox')[0];
    //Lightbox.click(box);
});