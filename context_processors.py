import django.conf
import django.http

def media_url(request):
    "Adds settings.MEDIA_URL to the context as MEDIA_URL."
    from django.conf import settings
    return {'MEDIA_URL': settings.MEDIA_URL}

def user(request):
    "Adds the request.user object to the context as 'user'."
    if type(request) is django.http.HttpRequest:
        return {'user': request.user}
    else:
        return {}

def current_url(request):
    "Adds the current URL to the context as 'current_url'."
    return {'current_url': request.get_full_path()}

def is_ajax(request):
    if request.GET.get('ajax', None) is not None:
        return {'is_ajax': True}
    else:
        return {'is_ajax': request.is_ajax()}
