(function(jQuery){

jQuery.fn.imageDropdown = function(options) {
    
    // Handle multiple objects.
    if (this.length > 1){
        this.each(function() { $(this).imageDropdown(options) });
        return this;
    }
    
    // Define default values for options.
	var defaults = {
        'selectList': undefined, // The list control that holds the options.
        'initialIndex': 0 // the index of the option to select on initialization
	};
	
    // Merge options and defaults.
	var opts = $.extend(defaults, options);
    
    // Track the index of the currently selected item
    var _selectedIndex;

    // Return the value (as specified by the data-value attribute) of the currently selected item.
    this.val = function(){
        return opts.selectList.children('li').eq(this.getSelectedIndex()).attr('data-value');
    }

    this.getSelectedIndex = function() {
        return _selectedIndex;
    }
    
    this.setSelectedIndex = function(index){
        
        // The element that will display the selection when the menu closes
        var selectedDisplayElem = this.children("span:first");
        
        // Copy the markup from the selected item to the display element.
        selectedDisplayElem.html(opts.selectList.children().eq(index).html());
        
        // If the display element now contains hidden elements, show only those hidden elements.
        // This allows us to show, for example, "None" when menu is open and "Select One" when it's closed.
        if (selectedDisplayElem.children(":hidden").length){
            selectedDisplayElem.children(":visible").remove();
            selectedDisplayElem.children().show();
        }
        
        _selectedIndex = index;
        
        // Call any event handlers that have been bound.
        this.trigger('change', index);
        
        return this;
    }
    
    this.reset = function(){
        this.setSelectedIndex(opts.initialIndex);
    }
    
    // Prevent page scrolling when dropdowns are focused.
    this.bind('keydown', 'up', function(event){return false;});
    this.bind('keydown', 'down', function(event){return false;});
    this.bind('keypress', 'up', function(event){return false;});
    this.bind('keypress', 'down', function(event){return false;});
    
    
    // Handle key strokes
    var keyupHandler = function(event) {
        var menuOpen = opts.selectList.is(":visible");
        var curIndex = 0;

        if (event.keyCode === 27) { // escape
            if (menuOpen) {
                self.close();
            }
        }
        if (event.keyCode === 13) { // return
            if (menuOpen) {
            }
            else {
                self.click();
            }
        }
        if (event.keyCode === 38 || event.keyCode === 37)  // up
        {
            if (menuOpen) {
                if (curIndex > 0) {

                }
            }
            else {
                newIndex = self.getSelectedIndex() - 1;
                self.setSelectedIndex(Math.max(newIndex, 0));
            }
        }
        else if (event.keyCode === 40 || event.keyCode === 39) // down
        {
            if (menuOpen) {
                
            }
            else {
                newIndex = self.getSelectedIndex() + 1;
                self.setSelectedIndex(Math.min(newIndex, opts.selectList.children().length - 1));
            }
        }
        return false;
    };
    
    this.disableKeys = function(){
        this.unbind('keyup', 'return', keyupHandler);
        this.unbind('keyup', 'esc', keyupHandler);
        this.unbind('keyup', 'up', keyupHandler);
        this.unbind('keyup', 'down', keyupHandler);
    }
    
    this.enableKeys = function(){
        this.bind('keyup', 'return', keyupHandler);
        this.bind('keyup', 'esc', keyupHandler);
        this.bind('keyup', 'up', keyupHandler);
        this.bind('keyup', 'down', keyupHandler);
    };
    this.enableKeys();
    
    this.bindHover = function(){
        $(this).hover(function(){
            self.find('.dropIcon').addClass('active');
        }, function(){ 
            self.find('.dropIcon').removeClass('active');
        });
    }
    this.bindHover();

	var clickHandler = function(){
        opts.selectList.show().focus();
        $(this).addClass("squareDown");
        self.find('.dropIcon').addClass('openActive');
    };

    $(this).click(clickHandler);
    
    opts.selectList.children('li').click(function(){
        if (closeTimeout){
            clearTimeout(closeTimeout);
        }
        // copy the selected option into the permanent display span.
        self.setSelectedIndex(opts.selectList.children().index(this));        
        var i = opts.selectList.children('ls').index($(this));

        self.close();
        self.focus();
    });
    
    $(this).focus(function(){
        // Disable hovering behavior while in focus.
        $(this).unbind('mouseenter mouseleave');
        self.find('.dropIcon').addClass('active');
    });
    
    var closeTimeout;
    $(this).blur(function(event){
        closeTimeout = setTimeout(
            function(){
                if (opts.selectList.is(":visibile"));
                    self.close();
                self.find('.dropIcon').removeClass('active openActive');
                // Renable hovering behavior.
                self.bindHover();
            }
        , 150);
    });
    
    this.close = function(){
        opts.selectList.hide();
        self.removeClass("squareDown");
        self.find('.dropIcon').removeClass('openActive');
        self.trigger('close');        
    };
    
    this.enable = function(){
        this.enableKeys();
        this.click(clickHandler);
        this.bindHover();
    };
    
    this.disable = function(){
        this.disableKeys();
        $(this).unbind('click mouseenter mouseleave');
    };
    
    this.setSelectedIndex(opts.initialIndex);

    var self = this;
	return this;
};          

jQuery.fn.extend(  {

});

})(jQuery);