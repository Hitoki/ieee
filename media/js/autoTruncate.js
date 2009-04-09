
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
    var matches = this.match(/(\S+\s+)(.+)/);
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
            alert('auto-truncate: must specify a length');
            return;
        }
        
        if (typeof options.word_boundary != 'boolean') {
            alert('auto-truncate: "word_boundary" must be a boolean');
            return;
        }
        
        if (typeof options.flyover != 'boolean') {
            alert('auto-truncate: "flyover" must be a boolean');
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

        var text = original_text = elem.text();
        
        // Check if the text is too long
        if (text.length > options.length) {
            elem.text('');
            var shortText;
            if (options.word_boundary) {
                // Split on a word boundary (ie. remove any leftover word part)
                shortText = '';
                [word, text] = text.popWord();
                while ($.trim(shortText + word).length <= options.length) {
                    shortText += word;
                    [word, text] = text.popWord();
                }
            } else {
                shortText = text.substr(0, options.length);
            }
            
            shortText = $.trim(shortText) + '...';
            
            var abbr = $('<abbr></abbr>').appendTo(elem);
            abbr.text(shortText);
            if (!options.no_tooltip) {
                abbr.attr('title', original_text);
            }
            
            if (options.flyover) {
                Flyover.attach(abbr, flyoverOptions);
            }
        }
        
    });
}
    
$(function() {
    autoTruncate($('.auto-truncate'));
    autoTruncate($('.auto-truncate-words'), {word_boundary:true} );
});
