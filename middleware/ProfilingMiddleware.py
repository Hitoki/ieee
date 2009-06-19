# Originally from http://www.djangosnippets.org/snippets/186/

import sys
import tempfile
import hotshot
import hotshot.stats
from django.conf import settings
from cStringIO import StringIO

class ProfileMiddleware(object):
    """
    Displays hotshot profiling for any view.
    http://yoursite.com/yourview/?prof

    Add the "prof" key to query string by appending ?prof (or &prof=)
    and you'll see the profiling results in your browser.
    It's set up to only be available in django's debug mode,
    but you really shouldn't add this middleware to any production configuration.
    * Only tested on Linux
    """
    def process_request(self, request):
        if settings.DEBUG and request.GET.has_key('prof'):
            self.tmpfile = tempfile.NamedTemporaryFile()
            temp_name = self.tmpfile.name
            self.tmpfile.close()
            self.prof = hotshot.Profile(temp_name)

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if settings.DEBUG and request.GET.has_key('prof'):
            return self.prof.runcall(callback, request, *callback_args, **callback_kwargs)

    def process_response(self, request, response):
        if settings.DEBUG and request.GET.has_key('prof'):
            self.prof.close()

            out = StringIO()
            old_stdout = sys.stdout
            sys.stdout = out

            stats = hotshot.stats.load(self.tmpfile.name)
            #stats.strip_dirs()
            stats.sort_stats('time', 'calls')
            stats.print_stats()

            sys.stdout = old_stdout
            stats_str = out.getvalue()

            if response and response.content and stats_str:
                response.content = "<pre>" + stats_str + "</pre>"

        return response

# From http://www.djangosnippets.org/snippets/727/

import sys
import cProfile
from cStringIO import StringIO
from django.conf import settings

import os

class CProfilerMiddleware(object):
    def process_view(self, request, callback, callback_args, callback_kwargs):
        if settings.DEBUG_WRITE_PROFILING or (settings.DEBUG and 'prof' in request.GET):
            self.profiler = cProfile.Profile()
            args = (request,) + callback_args
            return self.profiler.runcall(callback, *args, **callback_kwargs)

    def process_response(self, request, response):
        if settings.DEBUG and 'prof' in request.GET:
            self.profiler.create_stats()
            out = StringIO()
            old_stdout, sys.stdout = sys.stdout, out
            self.profiler.print_stats(1)
            sys.stdout = old_stdout
            response.content = '<h1>cProfile Output</h1>' \
                + '<pre>%s</pre>' % out.getvalue()
            
        elif settings.DEBUG_WRITE_PROFILING:
            
            url = request.get_full_path()
            
            if not url.startswith('/media'):
                
                self.profiler.create_stats()
                out = StringIO()
                old_stdout, sys.stdout = sys.stdout, out
                self.profiler.print_stats(1)
                sys.stdout = old_stdout
                
                import re
                seconds = re.search('in ([\d.]+) CPU seconds', out.getvalue()).group(1)
                
                path = os.path.join(os.path.dirname(__file__), '..', 'logs')
                if not os.path.exists(path):
                    os.mkdir(path)
                
                i = 0
                while True:
                    filename = os.path.join(path, 'log_%d.txt' % i)
                    if not os.path.exists(filename):
                        break
                    i += 1
                    
                file = open(filename, 'w')
                file.write('url: %s\n' % url)
                file.write(out.getvalue())
                
                from django.db import connection
                qstr = '<table border="1">\n'
                for query in connection.queries:
                    qstr += '<tr><td>%s</td><td>%s</td></tr>\n' % (query['time'], query['sql'])
                qstr += '</table>\n'
                
                file.write('SQL:\n')
                file.write(qstr)
                
                file.close()
                
                log_filename = os.path.join(path, 'index.csv')
                file = open(log_filename, 'a')
                file.write('%s\t%s\t%s\n' % (os.path.basename(filename), request.get_full_path(), seconds))
                file.close()

        return response

