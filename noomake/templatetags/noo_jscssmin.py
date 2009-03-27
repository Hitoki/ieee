#!/usr/bin/env python
# encoding: utf-8
"""
noo_jscssmin.py

Template tags to aggregate and minify JavaScript and CSS files, to improve
page load performance. It uses the Python port of Douglas Crockford's jsmin
for minifying JavaScript files.

While created the cached CSS and JS files, this code also creates gzipped
versions of the same, for server content negotiation.

CSS file aggregation searches for relative url() arguments in the source files
and translates them to absolute URLs in the output. The search uses a simple
regular expression rather than a full parser, but typical CSS is unlikely to
confuse it. If items referenced in the CSS file by their relative URLs stop
loading after enabling aggregation, check that the references use normal url()
syntax.

The JS processing alone improves overall page load performance by a factor of
2 on localhost, and probably helps a real server much more due to the latency
of 11 extra serialized script requests.

On an anonymous home page load (no TinyMCE), 207K of script was originally
downloaded, from 12 files. The template tag reduced this to 106K from 1 file,
or 31K with gzipping.

Modifications to files will be detected immediately, causing a new aggregate
cache to be generated. The cache will have a different name for each
modification, allowing us to set long expiry times for better client-side
caching, and also preventing users from ever having a stale version after we
push out updates.

Aggregation is automatically turned off when settings.DEBUG is on, but you can
enable it by adding settings to local_settings.py:

FORCE_AGGREGATE_CSS = True
FORCE_AGGREGATE_JS = True

There are optional settings for managing media in multi-directory projects,
where NooEngine may be installed outside the main project.

ADDITIONAL_MEDIA_ROOTS (optional) is a list of additional search paths for JS
and CSS aggregation.

CACHED_MEDIA_ROOT (optional) specifies where CSS and JS media caches are
placed. By default, they are placed in {MEDIA_ROOT}/caches.

CACHED_MEDIA_URL (optional) specifies how that directory appears in URLs.
It defaults to {MEDIA_URL}/caches/.

Created by Andrew P Shearer on 2008-04-27
Copyright (c) 2008-2009 Noosphere Networks, Inc. All rights reserved.
"""

__author__ = "Andrew Shearer"

import cgi
import os
import re
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape, escape
from django.utils.http import urlquote
from django.utils.safestring import mark_safe
from noomake import (jsmin, get_media_roots, expand_css_variables,
    is_js_aggregation_on, is_css_aggregation_on)
#from nooprofile import get_mce_plugin_list
    # TODO: Get rid of above import. It introduces a dependency
    # on nooprofile to noomake.

from ieeetags.logger import log
    
register = template.Library()

@register.tag('checkcssmin')
def checkcssmintag(parser, token):
    """
    {% checkcssmin as myboolvar %}
    
    Check whether CSS aggregation is turned on, and return the result
    in the named variable.
    """
    bits = token.split_contents()
    if len(bits) != 3 or bits[1] != 'as':
        raise template.TemplateSyntaxError(
            "checkcssmin syntax is {% checkcssmin as varname %}")
    return CachedSimpleSetterNode(bits[2], is_css_aggregation_on())

@register.tag('checkjsmin')
def checkjsmintag(parser, token):
    """
    {% checkjsmin as myboolvar %}
    
    Check whether JS aggregation is turned on, and return the result
    in the named variable.
    """
    bits = token.split_contents()
    if len(bits) != 3 or bits[1] != 'as':
        raise template.TemplateSyntaxError(
            "checkjsmin syntax is {% checkjsmin as varname %}")
    return CachedSimpleSetterNode(bits[2], is_js_aggregation_on())

@register.tag('jsmin')
def jsmintag(parser, token):
    """
    Insert a reference to an aggregated and cached JavaScript file
    made from the indicated source JavaScript files.
    
    If ``DEBUG`` is on in the site settings, aggregation is turned off to make
    debugging easier. (A regular script tag is inserted for each source file.)
    Setting ``FORCE_AGGREGATE_JS`` to True overrides this behavior.
    
    Example::
    
        <head>
            <title>My Page</title>
            {% jsmin js/myscript.js js/myscript2.js %}
        </head>
    
    when debug is on, inserts (with ``MY_MEDIA_URL`` substituted)::
    
        <script type="text/javascript" href="MY_MEDIA_URL/js/myscript.js"></script>
        <script type="text/javascript" href="MY_MEDIA_URL/js/myscript2.js"></script>
    
    when debug is off, inserts a reference to a cached compacted JS file::
    
        <script type="text/javascript" href="MY_MEDIA_URL/cachedjs/8fdsa23jc93.js"></script>
    
    """
    
    bits = token.split_contents()
    urls = [url.strip('"') for url in bits[1:]]
    return CachedJSNode(urls)

@register.tag('cssmin')
def cssmintag(parser, token):
    """
    Insert a reference to an aggregated, compacted, and cached CSS file
    made from the indicated source CSS files.
    
    If ``DEBUG`` is on in the site settings, aggregation is turned off to make
    debugging easier. (A regular CSS link is inserted for each source file.)
    Setting ``FORCE_AGGREGATE_CSS`` to True overrides this behavior.

    Example::
    
        <head>
            <title>My Page</title>
            {% cssmin media="screen,print" style.css style2.css %}
        </head>
    
    when debug is on, inserts (with ``MY_MEDIA_URL`` substituted)::
    
        <link rel="stylesheet" type="text/css" href="MY_MEDIA_URL/style.css" media="screen,print" />
        <link rel="stylesheet" type="text/css" href="MY_MEDIA_URL/style2.css" media="screen,print" />
    
    when debug is off, inserts a reference to a cached compacted CSS file::
    
        <link rel="stylesheet" type="text/css" href="MY_MEDIA_URL/caches/css/432143214f2.css" media="screen,print" />
    
    """
    
    #log('cssmintag()')
    
    bits = token.split_contents()
    urls = [url.strip('"') for url in bits[1:] if '=' not in url]
    attrtext = ' '.join(attr for attr in bits[1:] if '=' in attr)
    return CachedCSSNode(urls, attrtext)

@register.tag('mcemin')
def mcemintag(parser, token):
    """
    Insert a reference to an aggregated, compacted, and cached TinyMCE.

    Example::
    
        <script type="text/javascript">
            var mceUrl = {% mcemin en advanced safari,inlinepopups,linkdetail,spellchecker,caption,imagemanager,media,table,emotions %};
        </script>
    
    creates a url that jQuery can load to get all of tinymce::
    
        <script type="text/javascript">
            var mceUrl = "/site_media/caches/js/c77992ecbb2818fc83e1caa87e3a1757b.js";
        </script>
    
    the contents of the cached js file would include tinymce, and all
    necessary support files for themes/plugins/languages.

    """

    bits = token.split_contents()
    user = bits[1]
    languages = bits[2]
    themes = bits[3]
    return CachedMCENode(user, languages, themes)

def get_js_cache(sourceurls, root_paths=None):
    return get_cache(sourceurls, 'js', '.js', aggregate_js, root_paths)

def get_css_cache(sourceurls, root_paths=None):
    return get_cache(sourceurls, 'css', '.css', aggregate_css,
        root_paths)

def get_expanded_css_cache(sourceurls, root_paths=None):
    return get_cache(sourceurls, 'css', '.css', lambda source:
        expand_css_variables(source, _parse_css_vars()), aggregate=False)

def get_cache(sourceurls, cachedirname, extension, aggregator, root_paths=None,
    aggregate=True):
    from md5 import md5
    import os
    from django.conf import settings
    if root_paths is None:
        root_paths = get_media_roots()
    root_paths = [os.path.normpath(root_path) for root_path in root_paths]
    md5data = ''
    sourceurlsandpaths = []
    for url in sourceurls:
        md5data += url
        for root_path in root_paths:
            # if there's a variables.css, append its modified time to the md5
            # hash, so changes are captured
            vars_path = os.path.join(root_path,"css/variables.css")
            if os.path.exists(vars_path):
                md5data += str(os.path.getmtime(vars_path))
            
            filepath = os.path.normpath(os.path.join(root_path, url))
            if not os.path.exists(filepath):
                filepath = None
            else:
                break
        # TODO: check that normpath(filepath) is still within MEDIA_ROOT
        if not filepath:
            raise template.TemplateSyntaxError(
                'File not found in theme or main media directory: "%s"' % url)
        md5data += str(os.path.getmtime(filepath))
        
        sourceurlsandpaths.append((url, filepath))
    if aggregate:
        # use the aggregator callable to generate a single file
        cachefilename = 'c' + md5(md5data).hexdigest() + extension
        return [ensure_cache_file(cachedirname, cachefilename,
            lambda: aggregator(sourceurlsandpaths))]
    else:
        # use the aggregator callable on each file, creating processed versions
        # but basing them on the original filenames for ease of debugging
        return [ensure_cache_file(cachedirname,
            re.sub('[^A-Za-z0-9]+', '-', sourceurl)
            + '-' + md5(md5data).hexdigest() + extension,
            lambda: make_css_urls_absolute(aggregator(open(path, 'rb').read()),sourceurl)) #expand_css_variables(open(path, 'rb').read(), css_vars))
            for sourceurl, path in sourceurlsandpaths]

def get_cached_media_url():
    from django.conf import settings
    return getattr(settings, 'CACHED_MEDIA_URL',
        settings.MEDIA_URL.rstrip('/') + '/caches/')
    
def get_cached_media_root():
    from django.conf import settings
    return getattr(settings, 'CACHED_MEDIA_ROOT',
        os.path.join(settings.MEDIA_ROOT, 'caches'))

def ensure_cache_file(cachedirname, cachefilename, creator):
    """
    If the named cache file exists, do nothing.
    Otherwise create the file with the content specified by the 'creator'
    callable.
    Return the URL of the cache file.
    """
    cachefileurl = ''.join([get_cached_media_url(), cachedirname.rstrip('/'),
        '/', cachefilename])
    cacheroot = os.path.join(get_cached_media_root(), cachedirname)
    cachefilepath = os.path.join(cacheroot, cachefilename)
    if not os.path.exists(cachefilepath):
        if not os.path.exists(cacheroot):
            os.makedirs(cacheroot)
        cachecontent = creator() #processor(sourceurlsandpaths)
        outfile = open(cachefilepath, 'wb')
        outfile.write(cachecontent)
        outfile.close()
        from gzip import GzipFile
        outfile = GzipFile(cachefilepath + '.gz', 'w')
        outfile.write(cachecontent)
        outfile.close()
    return cachefileurl

def aggregate_js(urls_and_paths):
    """
    Returns a string of JavaScript that aggregates all the given
    JavaScript files (given by filesystem path) together.
    urls_and_paths is a list of (url, filesystem path) tuples.
    URL is intended as a base URL to interpret relative includes,
    so this function conforms to the same interface as aggregate_css,
    which needs to transform relative URLs.
    """
    contents = "\n".join([
        open(path, 'rb').read()
        for url, path in urls_and_paths])
    return jsmin.jsmin(contents)

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
def _parse_css_vars():
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

def aggregate_css(urls_and_paths):
    """
    Returns a string of CSS that aggregates all the given CSS files
    (given by filesystem path) together. urls_and_paths is a list of
    (url, filesystem path) tuples. The URL is useful as a basis for
    interpreting relative includes.
    
    Fix up embedded relative URLs in CSS files and expand variables.
    """
    css_vars = _parse_css_vars()
    return "\n".join([make_css_urls_absolute(expand_css_variables(open(path, 'rb').read(), css_vars), url)
        for url, path in urls_and_paths])

css_url_pattern = re.compile(r'url\s*\(\s*([^/][^\):]*)\s*\)', re.IGNORECASE)
def make_css_urls_absolute(source, url):
    """
    Fix up embedded relative URLs in CSS file data though a simple regular
    expression, in preparation for serving their content from a different
    location on the same server. The given url is used as a base for making
    relative URLs absolute. It in turn can be relative to MEDIA_URL.
    
    (The CSS files may not be in a position to use absolute URLs themselves,
    since they don't know the MEDIA_URL to use as a base.)
    
    For each "url(...)" in the original file, call urljoin to construct
    a new URL from settings.MEDIA_URL, the source stylesheet's URL path,
    and the argument to url().

    The regular expression used to find URLs isn't as accurate as a
    full CSS parser, but in practice CSS isn't likely to contain the
    pathological cases that would fool it. All of the existing CSS styles for
    the site were handled correctly the first time with this code.
    
    """
    from urlparse import urljoin
    from django.conf import settings
    url = urljoin(settings.MEDIA_URL, url)  # make base URL absolute
    return css_url_pattern.sub(
        lambda m: 'url(%s)' % urljoin(url, m.group(1)), source)

class CachedJSNode(template.Node):
    def __init__(self, urls):
        self.urls = urls
        self.is_aggregation_on = is_js_aggregation_on()
        
    def render(self, context):
        if self.is_aggregation_on:
            resulturls = get_js_cache(self.urls)
        else:
            from django.conf import settings
            resulturls = [settings.MEDIA_URL + url for url in self.urls]
        return ''.join([
            ('<script type="text/javascript" src="%s"></script>' % cgi.escape(url, 1))
            for url in resulturls])

class CachedSimpleSetterNode(template.Node):
    def __init__(self, varname, value):
        self.varname = varname
        self.value = value
        
    def render(self, context):
        context[self.varname] = self.value
        return ''

class CachedMCENode(template.Node):
    def __init__(self, user, languages, themes):
        self.languages = languages
        self.themes = themes
        self.user = template.Variable(user)

    def render(self, context):
        import os.path
        # generate a list of urls that need to be loaded
        current_user = self.user.resolve(context)
        languages = self.languages.split(',')
        plugins = get_mce_plugin_list(current_user).split(',')
        themes = self.themes.split(',')
        suffix = '_src'
        
        
        tinymce_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'php', 'tiny_mce')
        
        js_file_paths = [os.path.join("tiny_mce%s.js" % suffix)]
        
        js_file_paths.append("onaggregation.pre_plugin.js")

        for language in languages:
            js_file_paths.append(os.path.join("langs", "%s.js" % language))
            #content = content + open(os.path.join("langs", "%s.js" % language), 'r').read()

        for theme in themes:
            js_file_paths.append(os.path.join("themes", theme, "editor_template%s.js" % suffix))
            for language in languages:
                    js_file_paths.append(os.path.join("themes", theme, "langs", "%s.js" % language))

        for plugin in plugins:
            plugin_file = os.path.join("plugins", plugin, "editor_plugin%s.js" % suffix)
            if os.path.exists(os.path.join(tinymce_dir, plugin_file)):
                js_file_paths.append(plugin_file)

            for language in languages:
                plugin_lang_file = os.path.join("plugins", plugin, "langs", "%s.js" % language)
                if os.path.exists(os.path.join(tinymce_dir, plugin_lang_file)):
                    js_file_paths.append(plugin_lang_file)
        js_file_paths.append("onaggregation.post_plugin.js")
                
        resulturl = get_js_cache(js_file_paths, root_paths=[tinymce_dir])[0]
        return resulturl

class CachedCSSNode(template.Node):
    def __init__(self, urls, attrtext=''):
        #log('CachedCSSNode.__init__()')
        self.urls = urls
        self.attrtext = attrtext
        #log('  is_css_aggregation_on(): ' + str(is_css_aggregation_on()))
        self.is_aggregation_on = is_css_aggregation_on()
        self.are_variables_on = True
        
    def render(self, context):
        #log('CachedCSSNode.render()')
        #log('  self.is_aggregation_on: ' + str(self.is_aggregation_on))
        if self.is_aggregation_on:
            resulturls = get_css_cache(self.urls)
        elif self.are_variables_on:
            resulturls = get_expanded_css_cache(self.urls)
        else:
            from django.conf import settings
            resulturls = [settings.MEDIA_URL + url for url in self.urls]
        return ''.join([
            ('<link rel="stylesheet" type="text/css" href="%s" %s/>'
                % (url, (self.attrtext and self.attrtext + ' ') or ''))
            for url in resulturls])