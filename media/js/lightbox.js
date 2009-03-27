
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
    show: function(url) {
        var lightbox = this;
        if (!this.visible) {
            // Create the lightbox
            this.lightbox = $('<div id="lightbox"><div class="lightbox-background"></div><div class="lightbox-content"></div></div>').appendTo('body');
            this.lightboxBackground = $('<div class="lightbox-background"></div>').appendTo(this.lightbox);
            this.lightboxContent = $('<div class="lightbox-content"></div>').appendTo(this.lightbox);
            
            // Close the lightbox if user clicks outside the content area
            this.lightbox.click(function() {
                console.log('lightbox.click()');
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
        this.lightboxContent.load(url, null, function() { lightbox.onLoadContent(); } );
    },
    
    onLoadContent: function() {
        var lightbox = this;
        //console.log('onLoadContent()');
        //console.log('this: ' + this);
        //console.log('this.visible: ' + this.visible);
        if (this.visible) {
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
    },
    
    onFormResults: function(data) {
        if (this.visible) {
            this.lightboxContent.html(data);
            this.onLoadContent();
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