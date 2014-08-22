from django.conf import settings
from django.http import HttpRequest


def host_info(request):
    return {
        'host_info': "http%s://%s" % (("","s")[request.is_secure()],
                                      request.META["HTTP_HOST"]),
    }


def media_url(request):
    """
    Adds settings.MEDIA_URL to the context as MEDIA_URL.
    """
    return {
        'MEDIA_URL': settings.MEDIA_URL,
    }


def logo_href(request):

    if '/admin/' in request.path:
        value = '/admin/'
    elif '/textui/' in request.path:
        value = 'javascript:Tags.selectSociety("all",null,1);'
    else:
        value = '/'
    return {
        'LOGO_HREF': value,
    }


def external_help_url(request):
    """
    Adds settings.EXTERNAL_HELP_URL to the context as EXTERNAL_HELP_URL.
    """
    return {
        'EXTERNAL_HELP_URL': settings.EXTERNAL_HELP_URL,
    }


def user(request):
    """
    Adds the request.user object to the context as 'user'.
    """
    if type(request) is not HttpRequest:
        return {}
    return {
        'user': request.user,
    }


def current_url(request):
    """
    Adds the current URL to the context as 'current_url'.
    """
    return {
        'current_url': request.get_full_path(),
    }


def is_ajax(request):
    """
    Adds an "is_ajax" param to each template.
    Detects if the current request is an AJAX request.
    """
    return {
        'is_ajax': request.GET.get('ajax') is not None or request.is_ajax(),
    }


def survey(request):
    """
    Adds a flag value to the context if this user used the survey url to enter
    the site.
    """
    return {
        'survey': 'survey' in request.session,
    }


def django_settings(request):
    """
    Adds various settings variables to the current context for all pages.
    """
    return {
        'ENABLE_FIREBUG_LITE': settings.ENABLE_FIREBUG_LITE,
        'ENABLE_PROGRESSIVE_LOADING': settings.ENABLE_PROGRESSIVE_LOADING,
        'DEBUG': settings.DEBUG,
        'GA_SITE_NUM': settings.GA_SITE_NUM or 1,
    }


def total_tag_count(request):
    from models.node import Node
    from models.types import NodeType
    value = Node.objects.filter(node_type__name=NodeType.TAG).count() - 1
    return {
        'total_tag_count': value
    }


def socialauth_using_providers(request):
    return {
        'USING_GOOGLE_PROVIDER': settings.USING_GOOGLE_PROVIDER,
        'USING_LINKEDIN_PROVIDER': settings.USING_LINKEDIN_PROVIDER,
        'USING_FACEBOOK_PROVIDER': settings.USING_FACEBOOK_PROVIDER,
    }
