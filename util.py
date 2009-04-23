
import os.path

def relpath(file, path):
    """
    Returns an absolute, normalized path, relative to the current script.
    @param file should always be __file__ (ie. the current script)
    @param path the path relative to the the current script
    """
    return os.path.normpath(os.path.join(os.path.dirname(file), path))

def strip_bom(file):
    "Skips the first character in unicode file 'file' if it is the BOM."
    import codecs
    first_char = file.read(1)
    if first_char == unicode(codecs.BOM_UTF8, 'utf8'):
        # First char was BOM
        return True
    else:
        # First char was not BOM, seek back 1 char
        file.seek(-1, os.SEEK_CUR)
        return False

def begins_with(str1, prefix):
    return str1[:len(prefix)] == prefix

def ends_with(str1, prefix):
    return str1[-len(prefix):] == prefix

def current_server_url(request):
    #url = 
    print 'current_server_url()'
    for name, value in request.META.items():
        print '  %sm: %s' % (name, value)

class EndUserException(Exception):
    pass

def default_date_format(date1=None):
    import datetime
    if date1 is None:
        date1 = datetime.date.today()
    return date1.strftime('%a %b %d, %Y')

def default_time_format(time1=None):
    import time
    if time1 is None:
        time1 = time.localtime()
    return time.strftime('%I:%M %p', time1)

def default_datetime_format(datetime1=None):
    return default_date_format(datetime1) + ' ' + default_time_format(datetime1)
