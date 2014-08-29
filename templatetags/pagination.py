from django import template

register = template.Library()


@register.simple_tag
def pages(current_page, num_pages, url, max_pages=20):
    """
    Usage:
      {% pages [current_page] [num_pages] [url] [max_pages]%}

      max_pages is optional.

    Example:
      {% pages 2 4 "page.html?page={{ page }}" %}

    Output:
      <li><a href="page.html?page=1">1</a></li>
      <li class="selected"><a href="page.html?page=2">2</a></li>
      <li>...</li>
      <li><a href="page.html?page=4">4</a></li>

    Also adds ellipses when there are too many pages, keeping the selected
    page visible.
    """

    # Start with the full range
    start_page = 1
    end_page = num_pages

    if num_pages > max_pages:
        start_page = current_page - max_pages/2
        end_page = start_page + max_pages - 1

        if start_page < 1:
            start_page = 1
            end_page = start_page + max_pages - 1
        if end_page > num_pages:
            end_page = num_pages
            start_page = end_page - max_pages + 1

    #print 'start_page:', start_page
    #print 'end_page:', end_page

    url_template = template.Template(url)
    page_template = u'<li><a href="%s" %s>%s</a></li>'

    result = u''

    start_page1 = start_page
    end_page1 = end_page

    if start_page > 1:
        url1 = url_template.render(template.Context({'page': 1}))
        result += page_template % (url1, '', 1)

        url1 = url_template.render(template.Context({'page': start_page}))
        result += page_template % (url1, '', '...')

        start_page1 = start_page + 2

    if end_page < num_pages:
        end_page1 = end_page - 2

    for page in range(start_page1, end_page1+1):
        if int(page) == int(current_page):
            class1 = 'class="selected"'
        else:
            class1 = ''
        url1 = url_template.render(template.Context({'page': page}))
        result += page_template % (url1, class1, page)

    if end_page < num_pages:
        url1 = url_template.render(template.Context({'page': end_page}))
        result += page_template % (url1, '', '...')

        url1 = url_template.render(template.Context({'page': num_pages}))
        result += page_template % (url1, '', num_pages)

    return result
