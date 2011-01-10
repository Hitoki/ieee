
/**
 * Nootabs.js
 * Written by james Yoneda, 2008-10-22.
 * Handles automatic tabs through javascript.
 *
 **/
 
function Nootab(container, options) {
    //console.log("Nootab()");
    //console.log("container: " + container);
    //console.log("options:");
    //console.log(options);
    if (container) {
        this.setContainer(container, options);
    }
}

// Sets the container for this Nootab.
// Grabs all the menus and tabs, assigns classes, sets up events.
// 
Nootab.prototype.setContainer = function(container, options) {
    //console.log("Nootab.setContainer()");
    if (container) {
        //console.log("container: " + container);
        this.container = $(container);
        
        if (this.container.length != 1) {
            alert('Error in Nootab.setContainer(): container.length (' + this.container.length + ') should be 1.');
            return;
        }
        
        $(container).data('nootabs', this);
        
        if (!this.container[0].id)
            alert("nootabs: the container must have an id.");
        this.id = this.container[0].id;
        this.cookieName = 'nootab-current-tab-' + this.id;
        
        // Grab the embedded options
        var data = this.container.metadata();
        options = $.extend(options, data);
        
        this.options = {
            //bookmark: false,
            event: 'click'
            , reloadPage: false
            , useCookies: true
            , useHash: true
            , fullWidthMenus: false
            , fillerLine: false
            , disable: false
			, defaultTab: 1
			, onChangeTab: null
        };
        
        // Parse options
        
        //if ('bookmark' in options && typeof options.bookmark == 'boolean')
        //    this.options.bookmark = options.bookmark;
        if ('event' in options) {
            if (options.event == 'click' || options.event == 'mouseover')
                this.options.event = options.event;
        }
        if ('reloadPage' in options && typeof options.reloadPage == 'boolean')
            this.options.reloadPage = options.reloadPage;
        if ('disable' in options && typeof options.disable == 'boolean')
            this.options.disable = options.disable;
        if ('useCookies' in options && typeof options.useCookies == 'boolean')
            this.options.useCookies = options.useCookies;
        if ('fullWidthMenus' in options && typeof options.fullWidthMenus == 'boolean')
            this.options.fullWidthMenus = options.fullWidthMenus;
        if ('fillerLine' in options && typeof options.fillerLine == 'boolean')
            this.options.fillerLine = options.fillerLine;
        if ('defaultTab' in options)
            this.options.defaultTab = options.defaultTab;
        if ('useHash' in options)
            this.options.useHash = options.useHash;
        if ('onChangeTab' in options)
            this.options.onChangeTab = options.onChangeTab;
        
        //for (i in data)
            //console.log("data["+i+"]: " + data[i]);
            
        menus = this.container.children('.nootabs-menus').children('li');
        tabs = this.container.children('div');
        
        // NOTE: Don't check for equal number of menus & tabs if 'this.options.disable' is true (if no JS involved, page might have many menus & 1 tab
        if (!this.options.disable && menus.length != tabs.length) {
            alert('Nootab: Mismatched number of menus (' + menus.length + ') and tabs (' + tabs.length + ').');
        }
        
        this.tabs = [];
        this.selectedTab = null;
        
        if (!this.options.disable) {
            for (i=0; i<menus.length; i++) {
                this.addTab(menus[i], tabs[i]);
            }
        }
        
        $(menus[0]).addClass('nootabs-first-menu');
        
        if (this.options.fullWidthMenus) {
            // Menus are full width, calculate percentages so they fill the UL
            var width = Math.floor(100 / menus.length);
            menus.css('width', width + '%');
            // Make sure the last width adds up to 100%, not 99% due to rounding errors
            var lastWidth = width + (100 - width * menus.length);
            $(menus[menus.length-1]).css('width', lastWidth + '%');
        } else if (this.options.fillerLine) {
            // Menus are not full length, create a filler so the horizontal line extends to the entire width of the UL
            var ul = this.container.children('.nootabs-menus');
            var filler = $('<li class="nootabs-menu nootabs-menu-filler"></li>').appendTo(ul);
            
            var width = ul[0].offsetWidth;
            var menusWidth = 0;
            for (var i=0; i<menus.length; i++) {
                menusWidth += menus[i].offsetWidth;
            }
            var fillerWidth = width - menusWidth - 2;
            var fillerHeight = menus[0].offsetHeight - 1;
            
            filler.css('width', fillerWidth + 'px');
            filler.css('height', fillerHeight + 'px');
        }
        
        if (this.options.disable) {
            // This set of nootabs is disabled, simply ignore and don't attach any JS to the objects.
            return;
        }
        
        //if (this.options.bookmark) {
        //    AjaxHistory.registerCallback(this, 'onUrlHashChange');
        //}
        //
        //var hash = AjaxHistory.getHash();
        //var tab = this.getTabFromHash(hash);
        //if (tab !== null) {
        //    // Hash contained a tab, set that as the active one
        //    //console.log("got tab \"" + tab + "\"");
        //    var i = this.getTabFromId(tab);
        //    if (i !== null)
        //        //this.setTab(i);
        //} else {
        
        // Default to the first tab
		// NOTE: "defaultTab" starts at 1, while initialTab starts at 0
        var initialTab = this.options.defaultTab - 1;
		
        if (this.options.useHash) {
            // Parse the hash to find an initial tab
            var hash = window.location.hash;
            if (hash.length > 0) {
                // Remove leading '#' mark
                tabId = hash.replace(/^#tab-/, '');
                //var i = this.getTabFromId(hash + '-tab');
                var i = this.getTabFromId(tabId);
                if (i != null) {
                    initialTab = i;
                }
            }
            
        } else if (this.options.useCookies) {
            // If we have a cookie, use that for the initial tab instead
            if (this.getCookie() != null) {
                initialTab = this.getCookie();
            }
        }
        this.setTab(initialTab);
        
        //}
        
        // Show the nootab (initially hidden via CSS to avoid rendering before JS is done)
        this.container.css('display', 'block');
    }
}

Nootab.prototype.setCookie = function(index) {
    if (!$.cookie) {
        alert('Error in NooTab::setCookie(): $.cookie is null, nootabs.js requires jquery.cookie.js');
        return;
    }
    $.cookie(this.cookieName, index+"", {path:'/'} );
}

Nootab.prototype.getCookie = function() {
    if (!$.cookie) {
        alert('Error in NooTab::getCookie(): $.cookie is null, nootabs.js requires jquery.cookie.js');
        return;
    }
    
    if ($.cookie(this.cookieName) != null)
        return parseInt($.cookie(this.cookieName));
    else
        return null;
}

/*
// Check if the given hash string contains a tab instruction
Nootab.prototype.getTabFromHash = function(hash) {
    if (hash.substr(0, 4 + this.id.length) == 'tab-' + this.id) {
        // Hash contains a tab
        return hash.substr(4 + this.id.length + 1, hash.length-(4+this.id.length)-1);
    } else {
        return null;
    }
}
*/

//Nootab.prototype.onUrlHashChange = function() {
//    //console.log("onUrlHashChange()");
//    var hash = AjaxHistory.getHash();
//    var tab = this.getTabFromHash(hash);
//    if (tab !== null) {
//        // Hash contained a tab, set that as the active one
//        //console.log("got tab \"" + tab + "\"");
//        var i = this.getTabFromId(tab);
//        if (i !== null)
//            this.setTab(i);
//    }
//}

// Add a tab.
// Params:
//   menu - DOM LI object - the menu object.
//   tab - DOM DIV object - the tab object.
// 
Nootab.prototype.addTab = function(menu, tab) {
    var nootab = this;
    menu = $(menu);
    tab = $(tab);
    
    menu.addClass('nootabs-menu');
    var link = menu.children('a');
    if (link.length != 1)
        alert("Nootab: there are " + link.length + " links within the LI tag, require 1.");
    
    if (this.options.event == 'click') {
        link.click(function() {
            nootab.onSelectLink(this);
            return nootab.options.reloadPage;
        });
    } else if (this.options.event == 'mouseover') {
        link.mouseover(function() {
            nootab.onSelectLink(this);
        });
    }
    
    tab.addClass('nootabs-tab');
    this.tabs.push({
        id: tab[0].id,
        menu: menu,
        tab: tab
    });
}

// Set the active tab.
// Params:
//   index - integer for an index, or string for the tab id.
// 
Nootab.prototype.setTab = function(index, isUserClick) {
    if (typeof index == "string") {
        index = this.getTabFromId(index);
    }
    
    if (isUserClick == undefined) {
        isUserClick = false;
    }
    
    if (index !== null && index != this.selectedTab) {
        if (this.selectedTab != null) {
            this.tabs[this.selectedTab].menu.removeClass('nootabs-selected-menu');
            this.tabs[this.selectedTab].tab.removeClass('nootabs-selected-tab');
        }
        
        this.selectedTab = index;
        this.tabs[this.selectedTab].menu.addClass('nootabs-selected-menu');
        this.tabs[this.selectedTab].tab.addClass('nootabs-selected-tab');
        
        if (this.options.useCookies) {
            // Set the tab cookie
            if (this.getCookie() != index) {
                this.setCookie(index);
            }
        }
        
        if (this.options.useHash) {
            // If the tab has an id, set the hash
            if (this.tabs[this.selectedTab].tab.attr('id')) {
                //var hash = this.tabs[this.selectedTab].tab.attr('id').replace(/-tab$/, '');
                var hash = 'tab-' + this.tabs[this.selectedTab].tab.attr('id');
                window.location.hash = hash;
            }
        }
        
        //if (this.options.bookmark) {
        //    var hash = 'tab-' + this.id + "-" + this.tabs[this.selectedTab].id;
        //    AjaxHistory.setHash(hash);
        //}
        
        if (this.options.onChangeTab && isUserClick) {
            // Fire the onChangeTab callback only when the user explicitly changes the tab.
            this.options.onChangeTab(this);
        }
    }
}

// Gets the index of the tab given by the id.
// Params:
//   id - string - id of the tab DIV.
// 
Nootab.prototype.getTabFromId = function(id) {
    for (var i=0; i<this.tabs.length; i++) {
        if (this.tabs[i].id == id)
            return i;
    }
    return null;
}

// Gets the index of the tab given by the id.
// Params:
//   id - string - id of the tab DIV.
// 
Nootab.prototype.getMenuFromObj = function(obj) {
    for (var i=0; i<this.tabs.length; i++) {
        if (this.tabs[i].menu[0] == obj)
            return i;
    }
    return null;
}

// Called whena user clicks on a link within a menu.
// Sets the active tab for the given menu.
// 
Nootab.prototype.onSelectLink = function(link) {
    //console.log("onSelectLink()");
    if (this.options.reloadPage) {
        var nohash = window.location.href.replace(/#.+$/, '');
        //console.log("nohash: " + nohash);
        var i = this.getMenuFromObj(link.parentNode);
        var hash = 'tab-' + this.id + "-" + this.tabs[i].id;
        //console.log("hash: " + hash);
        console.log("nohash + hash: " + nohash + "#" + hash);
        //window.location = nohash + "#" + hash;
        window.location = nohash + "#" + hash;
    } else {
        var i = this.getMenuFromObj(link.parentNode);
        this.setTab(i, true);
    }
    $(document).trigger('onShowLightboxTab');
}

Nootab.prototype.getCurrentTabIndex = function() {
    return this.selectedTab;
}

Nootab.prototype.getCurrentTab = function() {
    return this.tabs[this.selectedTab];
}

////////////////////////////////////////////////////////////////////////////////

// Call this function to search for any tabs added after page load
function convertTabs() {
    $('.nootabs').each(function() {
        new Nootab(this);
    });
}

function attachNootabs(elem) {
    elem = $(elem);
    elem.find('.nootabs').each(function() {
        new Nootab(this);
    });
}

$(function() {
    $('.nootabs').each(function() {
        new Nootab(this);
    });
});
