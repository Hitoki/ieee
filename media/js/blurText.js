
function BlurText(elem, options) {
    var blurText = this;
    this.elem = $(elem);
    this.elem.data('blurText', this);
    
    this.options = extendExisting(
        {
            text: null,
            focusedClass: null,
            blurClass: null
        },
        this.elem.metadata(),
        options
    );
    
    this.elem.focus(function() {
        blurText.onFocus();
    });
    this.elem.blur(function() {
        blurText.onBlur();
    });
    this.onBlur();
}

BlurText.prototype.onFocus = function() {
    if (this.elem.attr('value') == this.options.text)
        this.elem.attr('value', '');
    
    if (this.options.focusedClass != null)
        this.elem.addClass(this.options.focusedClass);
    if (this.options.blurClass != null)
        this.elem.removeClass(this.options.blurClass);
}

BlurText.prototype.onBlur = function() {
    if ($.trim(this.elem.attr('value')) == '') {
        this.elem.attr('value', this.options.text);
        
        if (this.options.focusedClass != null)
            this.elem.removeClass(this.options.focusedClass);
        if (this.options.blurClass != null)
            this.elem.addClass(this.options.blurClass);
    }
    
}

BlurText.prototype.hasText = function() {
    return this.elem.attr('value') != this.options.text && $.trim(this.elem.attr('value')) != '';
}

var blurTexts = []

////////////////////////////////////////////////////////////////////////////////

function attachBlurTexts(elem) {
    elem = $(elem);
    elem.find('.blur-text').each(function() {
        blurTexts.push(new BlurText(this));
    });
}

$(function() {
    $('.blur-text').each(function() {
        blurTexts.push(new BlurText(this));
    });
});
