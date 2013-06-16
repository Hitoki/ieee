
// Similar to jQuery's $.extend(), except it only overwrites exising vars in obj1 with obj2 values
function extendExisting() {
    var args = extendExisting.arguments;
    
    if (!args[0])
        args[0] = {};
    
    for (var argnum=1; argnum<args.length; argnum++) {
        if (args[argnum]) {
            for (var i in args[0]) {
                if (i in args[argnum]) {
                    args[0][i] = args[argnum][i];
                }
            }
        }
    }
    
    return args[0];
}

// Pops the first word out of the given string.
// Returns an array:
//   The first element is the first word from the string
//   The second element is the remainder of the string (or '' if none)
String.prototype.popWord = function() {
    // NOTE: Can't use .+ for the rest of the string, since that doesn't include newlines.  Use [\S\s]+ instead.
    var matches = this.match(/(\S+\s+)([\S\s]+)/);
    //var matches = this.match(/(\S+\s+)(.+)/);
    if (!matches)
        return [this, ''];
    else
        return [matches[1], matches[2]];
}

function autoTruncate(elems, options) {
    elems = $(elems);
    elems.each(function() {
        var elem = $(this);
        
        // Use $.extend() instead of extendExisting() so we can pass-through the flyover options
        options = $.extend(
            {
                length: null,
                word_boundary: false,
                flyover: false,
                no_tooltip: false
            },
            options,
            elem.metadata()
        );
        
        if (options.length == null) {
            ajax_report_error('auto-truncate: must specify a length');
            return;
        }
        
        if (typeof options.word_boundary != 'boolean') {
            ajax_report_error('auto-truncate: "word_boundary" must be a boolean');
            return;
        }
        
        if (typeof options.flyover != 'boolean') {
            ajax_report_error('auto-truncate: "flyover" must be a boolean');
            return;
        }
        
        // Pass through flyover options
        var flyoverOptions = {};
        for (var name in options) {
            var matches = name.match(/^flyover(.+)/);
            if (matches) {
                // Get the flyover option without the 'flyover' prefix, and with the leading character made lowercase
                // Ex. 'flyoverOption' becomes 'option'
                var matches1 = matches[1].match(/(.)(.*)/);
                var flyoverName = matches1[1].toLowerCase() + matches1[2];
                flyoverOptions[flyoverName] = options[name];
            }
        }
        
        // NOTE: This crashes on Chrome:
        //var text = original_text = elem.text();
        var text = elem.text();
        var original_text = text;
        
        
        // Check if the text is too long
        if (text.length > options.length) {
            elem.text('');
            var shortText;
            if (options.word_boundary) {
                // Split on a word boundary (ie. remove any leftover word part)
                shortText = '';
                // NOTE: This crashes chrome:
                //[word, text] = text.popWord();
                var temp = text.popWord();
                word = temp[0];
                text = temp[1];
                
                while ($.trim(shortText + word).length <= options.length) {
                    shortText += word;
                    
                    if (text.length == 0) {
                        // NOTE: This shouldn't be needed, but it might catch some infinite loops
                        ajax_report_error('Error: autoTruncate(): text was "", breaking');
                        break;
                    }
                    
                    // NOTE: This crashes chrome:
                    //[word, text] = text.popWord();
                    var temp = text.popWord();
                    word = temp[0];
                    text = temp[1];
                }
            } else {
                shortText = text.substr(0, options.length);
            }
            
            shortText = $.trim(shortText) + '...';
            
            var abbr = $('<div class="truncatedText"></div>').appendTo(elem);
            abbr.text(shortText);
            if (!options.no_tooltip) {
                abbr.attr('title', original_text);
                abbr.addClass("flyover {position:'left-top', width:640, style:{tip:{corner:false}}, show:{delay:300}}");
            }
            
            if (options.flyover) {
                var content = {text: true, attr: 'title'};
                setupQtips($(abbr),content=content);
                //Flyover.attach(abbr, flyoverOptions);
            }
        }
        
    });
}
    
function attachAutoTruncates(elem) {
    elem = $(elem);
    elem.find('.auto-truncate').each(function() {
        autoTruncate(this);
    });
    elem.find('.auto-truncate-words').each(function() {
        autoTruncate(this, {word_boundary:true} );
    });
}

$(function() {
    autoTruncate($('.auto-truncate'));
    autoTruncate($('.auto-truncate-words'), {word_boundary:true} );
});
