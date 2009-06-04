import pprint
import os.path
import traceback
import settings
from django.core.mail import mail_admins

def get_current_url(request):
    if request.is_secure():
        url = 'https://'
    else:
        url = 'http://'
    url += request.META['HTTP_HOST'] + request.get_full_path()
    return url

class ExceptionMiddleware:
    
    def process_exception(self, request, exception):
        "Print or email exception info, depending on settings."
        message = getattr(exception, 'message', '')
        content = []
        content.append('')
        content.append('---------------------------------- EXCEPTION ----------------------------------')
        content.append('%s: %s' % (type(exception).__name__, message))
        content.append('%s' % get_current_url(request))
        content.append('')
        content.append('%s' % traceback.format_exc())
        content.append('REMOTE_ADDR: %s' % request.META['REMOTE_ADDR'])
        if not request.user.is_anonymous():
            content.append('request.user.username: %s' % request.user.username)
        for name, value in request.POST.items():
            content.append('request.POST[\'%s\']: %s' % (name, value))
        for name, value in request.GET.items():
            content.append('request.GET[\'%s\']: %s' % (name, value))
        content.append('-------------------------------------------------------------------------------')
        content = '\n'.join(content)
        
        if settings.DEBUG_PRINT_EXCEPTIONS:
            # Print the exception to the console
            print content
        
        if settings.DEBUG_EMAIL_EXCEPTIONS:
            # Email the exception to the admins
            subject = 'EXCEPTION: %s: %s at %s' % (type(exception).__name__, message, get_current_url(request))
            mail_admins(subject, content)
        
        return None
