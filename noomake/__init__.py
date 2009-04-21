"""
Tools for building the project. Includes:
 * Javascript and CSS aggregation/compaction
 * Release date updating
"""
import os
import os.path
import re
from PIL import Image, ImageOps
import Image
from django.conf import settings
from urlparse import urlparse, urlunparse 
import cgi

def _is_hotlinked(src):
    return src.find('http://') >= 0
    
def get_cached_image_tag(attrs):
    # we need to update the image tag to encode the size with the name, and point at the already resized image
    src = cgi.escape(get_attr_value('src', attrs), 1)  
    alt = get_attr_value('alt', attrs)
    width =  get_attr_value('width', attrs)
    height = get_attr_value('height', attrs)
    
    if _is_hotlinked(src):
        new_url = src
    else:    
        # change the path to point to the resized image that should have been generated
        # on publih, only if this is not a hotlinked image
        url_parts = urlparse(src)
        full_path = url_parts[2]                       
        fileandpath, ext = full_path.rsplit('.', 1)       
        path, filename = fileandpath.rsplit('/', 1)       
        new_dimensions = "x".join([width, height])
        new_filename = ".".join(["_".join([filename, new_dimensions]), ext]) 
        new_url = urlunparse((url_parts[0], url_parts[1], '%s%s' % (settings.RESIZED_MEDIA_URL, new_filename), '', '', ''))
        
    return '<img src="%(src)s" alt="%(alt)s" width="%(width)s" height="%(height)s" />' % \
        {'src': new_url, 'alt': alt, 'width': width, \
         'height': height}

def save_resized_image(attrs):
    src = cgi.escape(get_attr_value('src', attrs), 1)
    # leave hotlinked images alone
    if _is_hotlinked(src):
        return
        
    width =  get_attr_value('width', attrs)
    height = get_attr_value('height', attrs)
     
    cache_dir = settings.IMAGE_CACHE_ROOT
    origs_dir = settings.IMAGE_ORIG_ROOT
    
    image_name = list(src.split('/')).pop()
     
    file_part, extension = image_name.rsplit('.',1)
    cached_filename = "%s_%sx%s.%s" % (file_part, width, height, extension)
    # this is the final path and filename of the resized image
    cached_path = os.path.join(cache_dir, "%s" % (cached_filename,))
    
    #check if a cached copy at the current dimensions exists already -- this is just image_name, unaltered
    try:
         image = open(cached_path)
    except IOError:
        # no resized image exists at this size yet
        image = None                                   
        
    if image is None :
        # this image size doesn't exist yet
        # verify that we have an original of the requested image. a 500 is valid here,
        # if we can't find the original image
        orig = open(os.path.join(origs_dir, '.'.join([file_part, extension])))
        
        #resize the original
        x, y = (width, height,)
        #prevent a DOS attack from requesting absurdly large images
        if int(x) > settings.MAX_IMAGE_RESIZE_DIMENSION:
            x = settings.MAX_IMAGE_RESIZE_DIMENSION
        if int(y) > settings.MAX_IMAGE_RESIZE_DIMENSION:
            y = settings.MAX_IMAGE_RESIZE_DIMENSION
        unsized_image = Image.open(os.path.join(origs_dir, '.'.join([file_part, extension]))) 
        resized_image = unsized_image.resize((int(x), int(y)), Image.ANTIALIAS)
        resized_image.save(cached_path)
    return

def get_attr_value(attr_name, attrs):
    value = [value for name, value in attrs if name.lower() == attr_name]
    if value and value[0]:
        return value[0]
    else:
        # if attr was not found, silently return nothing
        return ""

def get_media_roots():
    """
    Get the media search path, the list of folders we'll use to search for
    CSS and JS files. This is a list instead of only settings.MEDIA_ROOT
    because of the theme system. Projects can also contribute more media roots
    to the search path through an ADDITIONAL_MEDIA_ROOTs setting in
    local_settings.py, which is useful for keeping their own media separate
    from NooEngine's.
    """
    from django.conf import settings
    result = []
    if getattr(settings, 'THEME_MEDIA_ROOT', None):
        result.append(settings.THEME_MEDIA_ROOT)
    result.append(settings.MEDIA_ROOT)
    result.extend(getattr(settings, 'ADDITIONAL_MEDIA_ROOTS', []))
    return result

def expand_css_variables(source, vars, var_name_order = [], current_name = ""):
    """
    Expand variables in the CSS file using the given dict for values.
    vars have syntax var(var-name).
    """
    def sub_var_name(match):
        """
        Don't allow variables to be referenced that hadn't been assigned when
        the current variable was created. This stops recursive definitions.

        Example:
        var1: var(var2);
        var2: var(var1);
        will result in:
        var1 = ''
        var2 = ''
        """
        if var_name_order.count(current_name) \
            and var_name_order.count(match.group(1)) \
            and var_name_order.index(match.group(1)) \
                    >= var_name_order.index(current_name):
            return ''
        return vars.get(match.group(1), '')
    return css_var_pattern.sub(lambda m: sub_var_name(m), source)

# TODO: make variable parsing more robust -- creating a class is probably
#       worthwhile, considering all the side-effects
# variables in the form
#   var(var-name)
css_var_pattern = re.compile(r'var\(([a-zA-Z0-9\-]+)\)', re.IGNORECASE)
# declarations in the form
#   var-name: value;
var_declaration_pattern = re.compile(r'([a-zA-Z\-0-9]+)\s*:\s*([a-zA-Z0-9_\-#% \(\)./]+);')
# /* comments */
comment_pattern = re.compile(r'/\*[^(\*/)]*\*/')
def parse_css_vars():
    import os
    import re

    css_vars = {}
    var_names_in_order = []
    root_paths = get_media_roots()
    root_paths = [os.path.normpath(root_path) for root_path in root_paths]
    # reversing allows templates to over-ride base variables
    root_paths.reverse()

    # first pass, to pull the variables out of the files
    nested_vars = []
    for root_path in root_paths:
        css_vars_path = os.path.join(root_path,"css/variables.css")
        if os.path.isfile(css_vars_path):
            var_values = var_declaration_pattern.findall(
                comment_pattern.sub('', open(css_vars_path, 'rb').read())
                )
            for pair in var_values:
                if css_var_pattern.search(pair[1]):
                    nested_vars.append(pair[0])
                css_vars[pair[0]] = pair[1]
                var_names_in_order.append(pair[0])
    # second+ passes
    # handle variables that have values that depend on other variables, ie:
    #   my-variable: 1px solid var(your-variable);
    while len(nested_vars) > 0:
        new_nested_vars = []
        for var_name in nested_vars:
            css_vars[var_name] = expand_css_variables(css_vars[var_name], css_vars, var_names_in_order, var_name)
            if css_var_pattern.search(css_vars[var_name]):
                new_nested_vars.append(var_name)
        nested_vars = new_nested_vars
    return css_vars

def is_js_aggregation_on():
    from django.conf import settings
    return not settings.DEBUG or getattr(settings, 'FORCE_AGGREGATE_JS', False)

def is_css_aggregation_on():
    #from ieeetags.logger import log
    #log('is_css_aggregation_on()')
    from django.conf import settings
    #log("  settings.DEBUG: %s" % str(settings.DEBUG))
    #log("  getattr(settings, 'FORCE_AGGREGATE_CSS', False): %s" % str(getattr(settings, 'FORCE_AGGREGATE_CSS', False)))
    return not settings.DEBUG or getattr(settings, 'FORCE_AGGREGATE_CSS', False)
