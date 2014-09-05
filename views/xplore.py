import cgi
import re
import socket
import urllib
import urllib2
import xml.dom.minidom
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import simplejson as json
from html2text import html2text
from HTMLParser import HTMLParseError
from logging import debug as log
from raven.contrib.django.raven_compat.models import client as raven_client

from decorators import optional_login_required as login_required
from models import UserExternalFavorites
from models.node import Node
import settings


XPLORE_SORT_AUTHOR = 'au'
XPLORE_SORT_TITLE = 'ti'
XPLORE_SORT_AUTHOR_AFFILIATIONS = 'cs'
XPLORE_SORT_PUBLICATION_TITLE = 'jn'
# NOTE: This causes an error on the xplore server.
#XPLORE_SORT_ARTICLE_NUMBER = 'an'
XPLORE_SORT_PUBLICATION_YEAR = 'py'

XPLORE_SORTS = [
    XPLORE_SORT_AUTHOR,
    XPLORE_SORT_TITLE,
    XPLORE_SORT_AUTHOR_AFFILIATIONS,
    XPLORE_SORT_PUBLICATION_TITLE,
    #XPLORE_SORT_ARTICLE_NUMBER,
    XPLORE_SORT_PUBLICATION_YEAR,
]


@login_required
def xplore_full_results(request, tag_id):
    """
    Returns full listing of IEEE xplore results for the given tag.
    """
    tag = Node.objects.get(id=tag_id)
    results, errors, total_results = _get_xplore_results(tag.name,
                                                         show_all=True)
    return render(request, 'xplore_full_results.html', {
        'tag': tag,
        'xplore_error': errors,
        'xplore_results': results,
        'totalfound': total_results,
    })


class XploreError(Exception):
    pass


def get_xplore_xml_tree(url, items_type):
    try:
        timeout = settings.EXTERNAL_XPLORE_TIMEOUT_SECS
        f = urllib2.urlopen(url, timeout=timeout)

        # Get the charset of the request and decode/re-encode the response text
        # into UTF-8 so we can parse it
        info = f.info()
        try:
            temp, charset = info['content-type'].split('charset=')
        except ValueError:
            charset = 'utf-8'
    except urllib2.URLError as e:
        if hasattr(e, 'reason') and isinstance(e.reason, socket.timeout):
            msg = "URLError: Request for %s timed out after %d seconds." % \
                  (items_type, settings.EXTERNAL_XPLORE_TIMEOUT_SECS)
            raven_client.captureMessage(msg, extra={"xplore_url": url})
        else:
            raven_client.captureMessage(e, extra={"xplore_url": url})
        raise XploreError('Error: Could not connect to the IEEE Xplore site'
                          ' to download %s.' % items_type)
    except KeyError:
        raise XploreError('Error: Could not determine content type of the'
                          ' IEEE Xplore response.')
    except socket.timeout:
        msg = "Request for %s timed out after %d seconds." % \
              (items_type, settings.EXTERNAL_XPLORE_TIMEOUT_SECS)
        raven_client.captureMessage(msg, extra={"xplore_url": url})
        raise XploreError('Error: Connection to IEEE Xplore timed out.')
    else:
        xml_body = f.read()
        f.close()
        xml_body = xml_body.decode(charset, 'replace').encode('utf-8')
        xml_tree = xml.dom.minidom.parseString(xml_body)
        return xml_tree


def _get_xplore_results(tag_name, highlight_search_term=True, show_all=False,
                        offset=0, sort=None, sort_desc=False, ctype=None,
                        recent=False, user=None):
    """
    Get xplore results for the given tag_name from the IEEE Xplore search
    gateway.  Searches all fields for the tag_name phrase, returns results.
    @return: a 3-tuple of (results, errors, total_results).  'errors' is a
    string of any errors that occurred, or None.  'total_results' is the
    total number of results (regardless of how many are returned in
    'results'.  'results' is an array of dicts:
        [
            {
                'name': ...
                'description': ...
                'url': ...
            },
            ...
        ]
    """
    if show_all:
        # Some arbitrarily big number...
        max_num_results = 10000
    elif recent:
        max_num_results = 1
    else:
        max_num_results = 10

    if sort is not None and sort not in XPLORE_SORTS:
        raise Exception('Unknown sort %r' % sort)

    params = {
        # Number of results
        'hc': max_num_results,
        # Specifies the result # to start from
        'rs': offset+1
    }

    if sort:
        params['sortfield'] = sort
    if sort_desc:
        params['sortorder'] = 'desc'
    if ctype:
        params['ctype'] = ctype

    tax_term_count = \
        Node.objects.filter(name=tag_name, is_taxonomy_term=True).count()

    # Different query parameter keys/values that return different result counts
    # Well, loop thru these in order until we get more than zero results
    # from xplore.
    tag_name_replaced_brackets = tag_name.encode('utf-8').\
        replace('(', '.LB.').replace(')', '.RB.')
    param_options = [  # todo: fix
        {'key': 'thsrsterms', 'value': '"%s"' % tag_name_replaced_brackets},
        # {'key': 'md', 'value': '"%s"' % tag_name_replaced_brackets},
        {'key': 'md', 'value': '%s' % tag_name_replaced_brackets},
    ]

    if not tax_term_count:
        # no need for thsrsterm so toss out the first item
        del param_options[0]

    for obj in param_options:
        # clear any previous values
        if 'thsrsterms' in params:
            del params['thsrsterms']
        if 'md' in params:
            del params['md']

        params[obj['key']] = obj['value']

        url = settings.EXTERNAL_XPLORE_URL + urllib.urlencode(params)

        if settings.DEBUG:
            log('xplore query: %s' % url)

        try:
            xml_tree = get_xplore_xml_tree(url, "Xplore articles")
        except XploreError as e:
            xplore_results = []
            xplore_error = e.message
            total_found = 0
            return xplore_results, xplore_error, total_found

        try:
            totalfound = int(getElementValueByTagName(xml_tree.documentElement,
                                                      'totalfound'))
        # If no records found Xplore will return xml like this and the int
        # parse with raise an exeption
        # <Error><![CDATA[Cannot go to record 1 since query only
        # returned 0 records]]></Error>
        except TypeError:
            # If there's any query param choice to try, do so.
            if obj != param_options[-1]:
                continue
            # Otherwise, give up.
            return [], 'No records found', 0

        if ctype == 'Educational Courses':
            external_resource_type = 'educational course'
        else:
            external_resource_type = 'article'

        xplore_error = None
        user_favorites = \
            UserExternalFavorites.objects.get_external_ids(
                external_resource_type, user)
        xplore_results = []
        nodes = xml_tree.documentElement.getElementsByTagName('document')
        for document1 in nodes:
            rank = getElementValueByTagName(document1, 'rank')
            title = getElementValueByTagName(document1, 'title')
            title = re.sub('<img [^>]*alt="(?P<alt>[^"]+)"[^>]*>',
                           '\g<alt>', title)
            abstract = getElementValueByTagName(document1, 'abstract')
            if abstract is not None:
                try:
                    abstract = html2text(abstract)
                except HTMLParseError:
                    pass
            pdf = getElementValueByTagName(document1, 'pdf')
            authors = getElementValueByTagName(document1, 'authors')
            pub_title = getElementValueByTagName(document1, 'pubtitle')
            pub_year = getElementValueByTagName(document1, 'py')

            m = re.search('\?arnumber=([\w\d]+)$', pdf)
            ext_id = m.group(1) if m else ''
            is_favorite = ext_id in user_favorites

            # Escape here, since we're going to output this as |safe
            # on the template
            # title = cgi.escape(title)
            if highlight_search_term:
                title = re.sub('(?i)(%s)' % tag_name,
                               r'<strong>\1</strong>',
                               title)
            result = {
                'rank': rank,
                'ext_id': ext_id,
                'name': title,
                'description': abstract,
                'url': pdf,
                'authors': authors,
                'pub_title': pub_title,
                'pub_year': pub_year,
                'external_resource_type': external_resource_type,
                'is_favorite': is_favorite,
            }
            xplore_results.append(result)

        return xplore_results, xplore_error, totalfound  # todo: fix


def getElementByTagName(node, tag_name):
    nodes = node.getElementsByTagName(tag_name)
    if len(nodes) == 0:
        return None
    elif len(nodes) == 1:
        return nodes[0]
    raise Exception('More than one element found for topic name "%s"' %
                    tag_name)


def getElementValueByTagName(node, tag_name):
    node1 = getElementByTagName(node, tag_name)
    if node1 is None:
        return None
    value = ''
    # print '  len(node1.childNodes): %r' % len(node1.childNodes)
    for child_node in node1.childNodes:
        # print '  child_node: %r' % child_node
        if child_node.nodeType == child_node.TEXT_NODE \
                or child_node.nodeType == child_node.CDATA_SECTION_NODE:
            value += child_node.nodeValue
    return value


@csrf_exempt
def ajax_recent_xplore(request):
    tag_name = request.POST.get('tag_name')

    params = {
        # Number of results
        'hc': 1,
        # Specifies the result # to start from
        'rs': 1
    }

    params['sortorder'] = 'desc'
    params['sortfield'] = XPLORE_SORT_PUBLICATION_YEAR

    tax_term_count = \
        Node.objects.filter(name=tag_name, is_taxonomy_term=True).count()

    tag_name_replaced_brackets = tag_name.encode('utf-8').\
        replace('(', '.LB.').replace(')', '.RB.')
    param_options = [
        {'key': 'thsrsterms', 'value': '"%s"' % tag_name_replaced_brackets},
        {'key': 'md', 'value': '"%s"' % tag_name_replaced_brackets},
        {'key': 'md', 'value': '%s' % tag_name_replaced_brackets}
    ]

    if not tax_term_count:
        # no need for thsrsterm so toss out the first item
        del param_options[0]

    xplore_error = None
    xplore_result = None
    for obj in param_options:
        # clear any previous values
        if 'thsrsterms' in params:
            del params['thsrsterms']
        if 'md' in params:
            del params['md']

        params[obj['key']] = obj['value']

        try:
            url = settings.EXTERNAL_XPLORE_URL + urllib.urlencode(params)
            xml_tree = get_xplore_xml_tree(url, "most recent Xplore article")
        except XploreError as e:
            xplore_error = e.message
        else:
            nodes = xml_tree.documentElement.getElementsByTagName('document')
            if len(nodes):
                title = getElementValueByTagName(nodes[0], 'title')
                title = re.sub('<img [^>]*alt="(?P<alt>[^"]+)"[^>]*>',
                               '\g<alt>', title)
                pdf = getElementValueByTagName(nodes[0], 'pdf')
                xplore_result = {
                    'name': title,
                    'url': pdf,
                }
                if request.user.is_authenticated():
                    m = re.search('\?arnumber=([\w\d]+)$', pdf)
                    ext_id = m.group(1) if m else ''
                    is_favorite = UserExternalFavorites.objects.filter(
                        user=request.user,
                        external_resource_type='article',
                        external_id=ext_id).exists()
                    xplore_result.update({
                        'externalId': ext_id,
                        'isFavorite': is_favorite,
                    })

    if not xplore_result:
        if xplore_error is not None:
            xplore_result = {
                'name': settings.XPLORE_TIMEOUT_RECENT_MESSAGE,
                'url': ''
            }
        else:
            xplore_result = None
    return HttpResponse(json.dumps(xplore_result), 'application/javascript')


@csrf_exempt
def ajax_xplore_results(request):
    """
    Shows the list of IEEE xplore articles for the given tag.
    @param tag_id: POST var, specifyies the tag.
    @param show_all: POST var, ("true" or "false"): if true, return all rows.
    @param offset: POST var, int: the row to start at.
    @param sort: POST var, the sorting field.
    @param sort_desc: POST var, the direction for sorting.
    @param token: POST var, the ajax token to pass through.
    @param ctype: POST var, the document type to search for. Blank equals all
        types.
    @return: HTML output of results.
    """
    tag_id = request.POST.get('tag_id')

    if tag_id is not None and tag_id != 'undefined':
        tag = Node.objects.get(id=tag_id)
        term = None
        name = tag.name
    else:
        assert False, 'Must specify tag_id.'

    show_all = (request.POST['show_all'] == 'true')
    offset = int(request.POST.get('offset', 0))
    sort = request.POST['sort']
    if sort == 'null':
        sort = None
    sort_desc = (request.POST['sort_desc'] == 'true')
    token = request.POST['token']
    ctype = request.POST.get('ctype')

    xplore_results, xplore_error, num_results = \
        _get_xplore_results(name, show_all=show_all, offset=offset, sort=sort,
                            sort_desc=sort_desc, ctype=ctype,
                            user=request.user)

    # DEBUG:
    #xplore_results = []
    #num_results = 0

    from django.template.loader import render_to_string
    content = render_to_string('include_xplore_results.html', {
        'MEDIA_URL': settings.MEDIA_URL,
        'xplore_results': xplore_results,
        'user': request.user,
        #'name': name,
        # TODO: This should use quote(), not replace()...
        #'search_term': name.replace(' ', '+'),
        #'xplore_error': xplore_error,
        #'totalfound': totalfound,
        #'show_all': show_all,
    })

    # DEBUG:
    #xplore_error = 'BAD ERROR.'

    data = {
        'num_results': num_results,
        'html': content,
        'xplore_error': xplore_error,
        'search_term': name,
        'token': token,
    }

    return HttpResponse(json.dumps(data), 'application/javascript')


def ajax_xplore_authors(tag_id, user=None):
    if tag_id is not None and tag_id != 'undefined':
        tag = Node.objects.get(id=tag_id)
        term = None
        tag_name = tag.name
    else:
        assert False, 'Must specify tag_id.'

    tag_name_replaced_brackets = tag_name.encode('utf-8').\
        replace('(', '.LB.').replace(')', '.RB.')

    params = {
        # No actual results, just the authors
        'hc': 0,
        'facet': 'd-au',
        'md': tag_name_replaced_brackets
    }

    url = settings.EXTERNAL_XPLORE_AUTHORS_URL + urllib.urlencode(params)

    if settings.DEBUG:
        log('xplore query: %s' % url)

    try:
        xml_tree = get_xplore_xml_tree(url, "Xplore authors")
    except XploreError as e:
        xplore_results = []
        xplore_error = e.message
        total_found = 0
        return xplore_results, xplore_error, total_found

    # try:
    #     totalfound = int(getElementValueByTagName(xml_tree.documentElement,
    #                                               'totalfound'))

    # # If no records found Xplore will return xml like this and the int
    # # parse with raise an exeption
    # # <Error><![CDATA[Cannot go to record 1 since query  only
    # # returned 0 records]]></Error>
    # except TypeError:
    #     # Otherwise, give up.
    #     return [], 'No records found', 0

    xplore_results = []
    if xml_tree.documentElement.nodeName != "Error":
        user_favorites = \
            UserExternalFavorites.objects.get_external_ids('author', user)
        author_nodes = xml_tree.documentElement.childNodes[5].childNodes[1].\
            getElementsByTagName('refinement')
        for author in author_nodes:
            name = getElementValueByTagName(author, 'name')
            name = re.sub('<img [^>]*alt="(?P<alt>[^"]+)"[^>]*>',
                          '\g<alt>', name)
            count = getElementValueByTagName(author, 'count')
            url = getElementValueByTagName(author, 'url')

            # massage the url
            url = url.replace('gateway/ipsSearch', 'search/searchresult')
            url = url.replace('&hc=0', '')
            url = url.replace('md=', 'queryText=')

            m = re.search('&refinements=(\d+)$', url)
            ext_id = m.group(1) if m else ''
            is_favorite = ext_id in user_favorites

            xplore_results.append({
                'ext_id': ext_id,
                'name': name,
                'count': count,
                'url': url,
                'is_favorite': is_favorite,
            })

    xplore_error = None
    return xplore_results, xplore_error, len(xplore_results)
