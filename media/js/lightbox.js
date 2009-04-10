
var Lightbox = {

    init: function() {
        this.visible = false;
        this.url = null;
    },

    // Clicked on a link, show the URL in the lightbox
    click: function(linkObj) {
        linkObj = $(linkObj);
        this.show(linkObj[0].href);
        return false;
    },
    
    // Show the given URL in the lightbox
    show: function(url, options) {
        var lightbox = this;
        if (!this.visible) {
            
            // Options
            this.options = extendExisting(
                {
                    closeOnClickOutside: true
                },
                options
            );
            
            // Create the lightbox
            this.lightbox = $('<div id="lightbox"></div>').appendTo('body');
            //<div class="lightbox-background"></div>
            this.lightboxBackground = $('<div class="lightbox-background"></div>').appendTo(this.lightbox);
            
            //this.lightboxContent = $('<div class="lightbox-content"></div>').appendTo(this.lightbox);
            this.lightboxContentOuterElem = $('<div class="vert-center-outer lightbox-content-outer"></div>').appendTo(this.lightbox);
            this.lightboxContentMiddleElem = $('<div class="vert-center-middle"></div>').appendTo(this.lightboxContentOuterElem);
            this.lightboxContent = $('<div class="vert-center-inner lightbox-content"></div>').appendTo(this.lightboxContentMiddleElem);
            
            // Close the lightbox if user clicks outside the content area
            this.lightbox.click(function() {
                console.log('lightbox.click()');
                if (lightbox.options.closeOnClickOutside)
                    lightbox.hide();
            });
            this.lightboxContent.click(function(e) {
                console.log('lightboxContent.click()');
                e.stopPropagation();
            });
            
            this.visible = true;
            this.updateScrollPos();
        }
        
        //this.lightbox.clear();
        $.get(url, null, function(data) { lightbox.onLoadContent(data); }, 'text');
        //this.lightboxContent.load(url, null, function() { lightbox.onLoadContent(); } );
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
                
                // Attach any multsearch objects
                if (attachMultiSearches) {
                    attachMultiSearches(this.lightboxContent);
                }
                
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
            var scrollTop = $(window).scrollTop();
            var scrollLeft = $(window).scrollLeft();
            this.lightbox.css('top', scrollTop);
            this.lightbox.css('left', scrollLeft);
        }
    }

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