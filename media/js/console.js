/**
 * Emulation of the console.log for IE users.
 * Shows a semi-transparent log window on top of the page contents.
 */

if ($.browser.msie) {
    // Show/hide the log window when user presses F12, just like Firebug on Firefox
    document.onkeydown = function() {
        if (window.event.keyCode == 123) {
            // Pressed F12, show the log box
            console.toggle();
            return false;
        }
    }
}
 
if (typeof console == "undefined") {
    console = {
        logWindow: null,
        
        messages: [],
        
        init: function() {
            this.createLogWindow();
            if (this.messages.length > 0) {
                for (var i in this.messages) {
                    this.log(this.messages[i]);
                }
            }
        },
        
        createLogWindow: function() {
            if ( this.logWindow == null ) {
                var opacity = .8;
                
                this.logWindow = document.createElement("div");
                document.body.appendChild(this.logWindow);
                this.logWindow.style.fontFamily = "tahoma";
                this.logWindow.style.fontSize = "8pt";
                this.logWindow.style.width = "100%";
                this.logWindow.style.height = "300px";
                this.logWindow.style.border = "1px solid silver";
                this.logWindow.style.background = "#eee";
                this.logWindow.style.overflow = "auto";
                this.logWindow.style.lineHeight = "1.2em";
                this.logWindow.style.position = "absolute";
                this.logWindow.style.padding = "5px";
                this.logWindow.style.bottom = "0px";
                this.logWindow.style.left = "0px";
                this.logWindow.style.opacity = opacity;
                this.logWindow.style.filter = "alpha(opacity=" + opacity*100 + ")";
                this.logWindow.style.color = "black";
                this.logWindow.style.textAlign = "left";
                this.logWindow.style.zIndex = "10000";
                this.logWindow.style.display = "none";
            }
        },
        
        show: function() {
            this.createLogWindow();
            this.logWindow.style.display = "block";
        },
        
        hide: function() {
            this.createLogWindow();
            this.logWindow.style.display = "none";
        },
        
        toggle: function() {
            if ($(this.logWindow).css("display") == "block")
                this.hide();
            else
                this.show();
        },
        
        log: function(msg) {
            if (this.logWindow == null) {
                this.messages[this.messages.length] = msg;
            } else {
                if (typeof msg == "object") {
                    if (typeof msg.toString != "undefined") {
                        msg = msg.toString();
                    } else {
                        msg = typeof msg;
                    }
                }
                
                msg = msg.replace( /\n/, "<br/>\n" );
                
                this.logWindow.appendChild(document.createTextNode(msg));
                this.logWindow.appendChild(document.createElement("br"));
                // Auto-scroll the log window to the bottom
                this.logWindow.scrollTop = 10000;
            }
        }
    };
    
    $(function() {
        console.log("Started log.");
        console.init();
    });
}

