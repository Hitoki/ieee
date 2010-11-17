#!/usr/bin/python

import os.path

# Django util functions --------------------------------------------------------

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
        #file.seek(-1, os.SEEK_CUR)
        
        # NOTE: This is for Python 2.4 compatability
        SEEK_CUR = 1
        file.seek(-1, SEEK_CUR)
        return False

def begins_with(str1, prefix):
    'DEPRECATED: This should be replaced with x.beginswith(...) instead.'
    return str1[:len(prefix)] == prefix

class EndUserException(Exception):
    pass

def default_date_format(date1=None):
    'Formats a date.'
    import datetime
    if date1 is None:
        date1 = datetime.date.today()
    return date1.strftime('%a %b %d, %Y')

def default_time_format(time1=None):
    'Formats a time.'
    import time
    if time1 is None:
        time1 = time.localtime()
    return time.strftime('%I:%M %p', time1)

def default_datetime_format(datetime1=None):
    'Formats a date/time.'
    return default_date_format(datetime1) + ' ' + default_time_format(datetime1)

def generate_password(length=8, chars='all'):
    '''
    Creates a random string useful for passwords.
    @param length: The number of chars for this password.
    @param chars: The charset to use, can be ALPHA_LOWER, ALPHA_UPPER, ALPHA, NUMERIC, SYMBOLS, SYMBOLS2, or ALL.
    '''
    ALPHA_LOWER = 'abcdefghijklmnopqrstuvwxyz'
    ALPHA_UPPER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    ALPHA = ALPHA_LOWER + ALPHA_UPPER
    NUMERIC = '0123456789'
    SYMBOLS = '~!@#$%^&*()_+`-=,./;\'[]\\<>?:"{}|'
    SYMBOLS2 = '~!@#$%^&*()_+-=./;\[]\\<>?:{}|'
    ALL = ALPHA + NUMERIC + SYMBOLS
    
    import random
    
    if chars == 'all':
        CHARS = ALL
    elif chars == 'alphanumeric':
        CHARS = ALPHA + NUMERIC
    elif chars == 'alpha':
        CHARS = ALPHA
    elif chars == 'numeric':
        CHARS = NUMERIC
    elif chars == 'loweralpha':
        CHARS = ALPHA_LOWER
    elif chars == 'loweralphanumeric':
        CHARS = ALPHA_LOWER + NUMERIC
    elif chars == 'upperalpha':
        CHARS = ALPHA_UPPER
    elif chars == 'upperalphanumeric':
        CHARS = ALPHA_UPPER + NUMERIC
    else:
        raise Exception('Unknown chars "%s"' % chars)
    
    passwd = ''
    for i in range(length):
        passwd += random.choice(CHARS)
    return passwd

def generate_words(min, max, chars='loweralpha'):
    'Generates random strings of chars, for testing.'
    import random
    length = random.randint(min, max)
    string = generate_password(length, chars)
    i = 0
    while i < len(string):
        i += random.randint(2, 10)
        string = string[:i] + ' ' + string[i:]
    return string

from UserDict import UserDict

class odict(UserDict):
    'Represents an ordered dict.  Normal dict objects do not maintain order.'
    
    def __init__(self, dict = None):
        self._keys = []
        UserDict.__init__(self, dict)

    def __delitem__(self, key):
        UserDict.__delitem__(self, key)
        self._keys.remove(key)

    def __setitem__(self, key, item):
        UserDict.__setitem__(self, key, item)
        if key not in self._keys: self._keys.append(key)

    def clear(self):
        UserDict.clear(self)
        self._keys = []

    def copy(self):
        dict = UserDict.copy(self)
        dict._keys = self._keys[:]
        return dict

    def items(self):
        return zip(self._keys, self.values())

    def keys(self):
        return self._keys

    def popitem(self):
        try:
            key = self._keys[-1]
        except IndexError:
            raise KeyError('dictionary is empty')

        val = self[key]
        del self[key]

        return (key, val)

    def setdefault(self, key, failobj = None):
        UserDict.setdefault(self, key, failobj)
        if key not in self._keys: self._keys.append(key)

    def update(self, dict):
        UserDict.update(self, dict)
        for key in dict.keys():
            if key not in self._keys: self._keys.append(key)

    def values(self):
        return map(self.get, self._keys)

def group_conferences_by_series(resources, include_current_conference=False):
    '''
    For a sequence of resources, groups any conferences in the same series together.
        -Loop through each conference series
        -If the 
    '''
    
    resources = list(resources)
    
    # Create a dict of series with all matching conferences from the list.
    series_conferences = {}
    for resource in resources:
        if resource.conference_series != '':
            if resource.conference_series not in series_conferences:
                series_conferences[resource.conference_series] = []
            series_conferences[resource.conference_series].append(resource)
    
    # Loop through all conferences in each series, remove them from the main list unless they're the current conference.
    for series, conferences in series_conferences.items():
        import datetime
        
        # Find the most recent conference for each series
        current_year = datetime.datetime.now().year
        conferences.sort(key=lambda obj: obj.year)
        
        # Choose the next future conference
        current_conference = None
        for conference in conferences:
            if conference.year >= current_year:
                current_conference = conference
                break
        
        if current_conference is None:
            # Choose the most recent past conference (if there are any)
            if len(conferences) > 0:
                current_conference = conferences[len(conferences)-1]
        
        assert current_conference is not None
        
        i = 0
        while i < len(resources):
            if resources[i] == current_conference:
                # Found the current conference in a series
                    
                resources[i].is_current_conference = True
                other_conferences = series_conferences[resources[i].conference_series]
                
                if not include_current_conference:
                    other_conferences1 = []
                    for conference in other_conferences:
                        if conference != current_conference:
                            other_conferences1.append(conference)
                    other_conferences = other_conferences1
                
                # Sort the other conferences by year latest to earliest.
                other_conferences = sorted(other_conferences, key=lambda resource: resource.year, reverse=True)
                
                resources[i].other_conferences = other_conferences
                i += 1
            elif resources[i] in conferences:
                # Remove all the non-current conferences
                del resources[i] # warning: altering collection while looping through it.
            else:
                # Found a non-series resource, just ignore it
                i += 1
    return resources

def word_wrap(string, max_chars):
    'Breaks up a string into separate lines, wrapping at word boundaries.'
    import re
    
    lines = [string]
    
    # Loop while the latest line has more than max_chars chars...
    while len(lines[len(lines)-1]) > max_chars:
        index = len(lines)-1
        expr = re.compile(r'\b')
        rline = lines[index][::-1]
        start_pos = len(lines[index]) - 20
        match = expr.search(rline, start_pos)
        if match is not None:
            pos = len(lines[index]) - match.start()
            line = lines[index]
            lines[index] = line[:pos]
            lines.append(line[pos:])
            
    result = '\n'.join(lines)
    return result

def profiler(view_func):
    '''
    Decorator to use for profiling a specific view.  Use like:
        @profiler
        def your_view(request):
            ...
    Will output profiler data files to the folder set in settings.PROFILER_OUTPUT_ROOT.
    By default, filename is [function_name] + [time].
    Outputs 3 formats:
        .txt - printed stats summary.
        .profile_out - binary python profiler output.
        .kcachegrind - kchachegrind-compatible output.
    '''
    #print 'profiler()'
    def _inner(*args, **kwargs):
        try:
            # For Python 2.5+:
            import cProfile as profile
        except ImportError:
            # For Python 2.4:
            import profile
            
        import settings
        import time
        import sys
        
        # NOTE: Must use this, or the 'filename' global/local var gets messed up.
        #filename2 = filename
        filename2 = None
        
        #print '_inner()'
        
        if filename2 is None:
            # Default to <function_name>_<time>.txt and .out
            filename2 = '%s_%s' % (view_func.__name__, time.time())
            
        filename_full = os.path.join(settings.PROFILER_OUTPUT_ROOT, filename2)
        #print 'filename2: %r' %filename2
        #print 'filename_full: %r' %filename_full
            
        if settings.PROFILER_OUTPUT_ROOT is None:
            raise Exception('settings.PROFILER_OUTPUT_ROOT must be set to save profiler output.')
        elif not os.path.exists(settings.PROFILER_OUTPUT_ROOT):
            os.mkdir(settings.PROFILER_OUTPUT_ROOT)
            #raise Exception('The settings.PROFILER_OUTPUT_ROOT folder %r does not exist.' % settings.PROFILER_OUTPUT_ROOT)
        
        #print '  view_func: %r' % view_func
        #print '  args: %s' % repr(args)
        #print '  kwargs: %s' % repr(kwargs)
        #print '  ----------'
        #response = view_func(*args, **kwargs)
        
        
        if settings.PROFILER_OUTPUT_LINEBYLINE:
            import line_profiler
            prof = line_profiler.LineProfiler(view_func)
            
            response = prof.runcall(view_func, *args, **kwargs )
            #print 'response: %r' % response
            
            # Line-by-line profiler
            file1 = open(filename_full + '.lineprofiler.txt', 'w')
            
            #prof.print_stats(file1)
            
            stats = prof.get_stats()
            #line_profiler.show_text(stats.timings, stats.unit, stream=file1)
            
            def show_text2(stats, unit, stream=None):
                """ Show text for the given timings.
                """
                if stream is None:
                    stream = sys.stdout
                #print >>stream, 'Timer unit: %g s' % unit
                #print >>stream, ''
                for (fn, lineno, name), timings in sorted(stats.items()):
                    show_func2(fn, lineno, name, stats[fn, lineno, name], unit, stream=stream)
                
            def show_func2(filename, start_lineno, func_name, timings, unit, stream=None):
                """ Show results for a single function.
                """
                from line_profiler import linecache, inspect
                
                if stream is None:
                    stream = sys.stdout
                print >>stream, "File: %s" % filename
                print >>stream, "Function: %s at line %s" % (func_name, start_lineno)
                template = '%6s %9s %12s %8s %8s  %-s'
                d = {}
                total_time = 0.0
                linenos = []
                for lineno, nhits, time in timings:
                    total_time += time
                    linenos.append(lineno)
                print >>stream, "Total time: %g s" % (total_time * unit)
                if not os.path.exists(filename):
                    print >>stream, ""
                    print >>stream, "Could not find file %s" % filename
                    print >>stream, "Are you sure you are running this program from the same directory"
                    print >>stream, "that you ran the profiler from?"
                    print >>stream, "Continuing without the function's contents."
                    # Fake empty lines so we can see the timings, if not the code.
                    nlines = max(linenos) - min(min(linenos), start_lineno) + 1
                    sublines = [''] * nlines
                else:
                    all_lines = linecache.getlines(filename)
                    sublines = inspect.getblock(all_lines[start_lineno-1:])
                for lineno, nhits, time in timings:
                    d[lineno] = (nhits, time, '%5.1f' % (float(time) / nhits),
                        '%5.1f' % (100*time / total_time))
                linenos = range(start_lineno, start_lineno + len(sublines))
                empty = ('', '', '', '')
                header = template % ('Line #', 'Hits', 'Time', 'Per Hit', '% Time', 
                    'Line Contents')
                print >>stream, ""
                print >>stream, header
                print >>stream, '=' * len(header)
                
                for lineno, line in zip(linenos, sublines):
                    nhits, time, per_hit, percent = d.get(lineno, empty)
                    
                    if per_hit != '':
                        per_hit = round(float(per_hit) * unit, 2)
                        if per_hit == 0:
                            per_hit = '-'
                        else:
                            per_hit = '%0.2f' % per_hit
                        
                    if time != '':
                        time = round(float(time) * unit, 2)
                        if time == 0:
                            time = '-'
                        else:
                            time = '%0.2f' % time
                    
                    if percent != '' and float(percent) == 0:
                        percent = '-'
                    
                    print >>stream, template % (lineno, nhits, time, per_hit, percent,
                        line.rstrip('\n').rstrip('\r'))
                print >>stream, ""
            
            show_text2(stats.timings, stats.unit, stream=file1)
            
            del file1
        
        else:
            
            # Other (not line-by-line) profilers.
            
            prof = profile.Profile()
            
            response = prof.runcall(view_func, *args, **kwargs )
            #print 'response: %r' % response
            
            if hasattr(settings, 'PROFILER_OUTPUT_TXT') and settings.PROFILER_OUTPUT_TXT:
                # Save text output.
                file1 = open(filename_full + '.txt', 'w')
                old_stdout = sys.stdout
                sys.stdout = file1
                # Internal Time
                #prof.print_stats(sort=1)
                # Cumulative
                prof.print_stats(sort=2)
                sys.stdout = old_stdout
                del file1
            
            if (hasattr(settings, 'PROFILER_OUTPUT_BINARY') and settings.PROFILER_OUTPUT_BINARY) or (hasattr(settings, 'PROFILER_OUTPUT_PNG') and settings.PROFILER_OUTPUT_PNG):
                # Save the binary output.
                prof.dump_stats(filename_full + '.profile_out')
                
                if hasattr(settings, 'PROFILER_OUTPUT_PNG') and settings.PROFILER_OUTPUT_PNG:
                    # Create the PNG callgraph image.
                    os.system('%s -f pstats %s | dot -Tpng -o %s 2>NUL' % (relpath(__file__, 'scripts/gprof2dot.py'), filename_full + '.profile_out', filename_full + '.png'))
                
                if not hasattr(settings, 'PROFILER_OUTPUT_BINARY') or not settings.PROFILER_OUTPUT_BINARY:
                    # We only wanted the PNG file, delete the binary file now that we're done with it.
                    os.remove(filename_full + '.profile_out')
            
            if hasattr(settings, 'PROFILER_OUTPUT_KCACHEGRIND') and settings.PROFILER_OUTPUT_KCACHEGRIND:
                # Save kcachegrind-compatible output.
                if hasattr(prof, 'getstats'):
                    import lsprofcalltree
                    k = lsprofcalltree.KCacheGrind(prof)
                    file1 = open(filename_full + '.kcachegrind', 'w')
                    k.output(file1)
                    del file1
        
        #print '  ----------'
        #print '~_inner()'
        return response
    return _inner

def truncate_link_list(items, output_func, plain_output_func, max_chars, tag=None, tab_name=None):
    """
    Takes a list of items and outputs links.  If the list is > max_chars, the list is truncated with '...(10 more)' appended.
    @param items: the list of items
    @param output_func: the HTML output formatting function, takes one item as its argument
    @param output_func: the Plaintext output formatting function, takes one item as its argument.  This is used to determine the content length (w/o HTML markup tags)
    @param max_chars: the maximum length of the output, not including the '... (X more)' if necessary
    """
    print 'truncate_link_list()'
    print '  tag: %r' % tag
    items_str = ''
    items_plaintext = ''
    
    for i in range(len(items)):
        item = items[i]
        if items_str != '':
            items_plaintext += ', '
            
        str1 = output_func(item)
        items_plaintext += plain_output_func(item)
        
        if len(items_plaintext) > max_chars:
            # check if tab_name exists as to not mess up clusters
            if tab_name is None:
                items_str += ' ... (%s more)' % (len(items) - i)
            else:
                if tag is not None:
                    items_str += ' ... (%s more - <a href="javascript:Tags.selectTag(%s, &quot;%s&quot;);">show all</a>)' % (len(items) - i, tag.id, tab_name)
                else:
                    items_str += ' ... (%s more)' % (len(items) - i)
            break
        else:
            if items_str != '':
                items_str += ', '
            items_str += str1
    
    return items_str

def get_min_max(list, attr):
    '''
    Finds the min and max value of the attr attribute of each item in the list.
    @param list: the list of items.
    @param attr: the name of the attribute to check the value.
    @return: A 2-tuple (min, max).
    '''
    min1 = None
    max1 = None
    for item in list:
        if min1 is None or getattr(item, attr) < min1:
            min1 = getattr(item, attr)
        if max1 is None or getattr(item, attr) > max1:
            max1 = getattr(item, attr)
    return (min1, max1)

def send_admin_email(subject, body):
    'Sends an email to the admins.'
    import settings
    from django.core.mail import send_mail
    
    emails = [temp[1] for temp in settings.ADMINS]
    try:
        send_mail(subject, message, settings.SERVER_EMAIL, emails)
    except Exception, e:
        # Silent fail.
        pass
    
# Command line util functions --------------------------------------------------

import subprocess
import settings
from getopt import getopt
from getopt import getopt
import settings
import subprocess
import sys

def _run_mysql_cmd(cmd):
    args = [
        'mysql',
        '--user=%s' % settings.DATABASE_USER,
        '--password=%s' % settings.DATABASE_PASSWORD,
        '%s' % settings.DATABASE_NAME,
        '-e',
        cmd,
    ]
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result = process.communicate()[0]
    #print 'stderr:', process.communicate()[1]
    return result
    
def create_db():
    import getpass
    
    password = getpass.getpass('Enter mysql root password:')
    
    # Drop the DB & user
    print 'Dropping database %s' % settings.DATABASE_NAME
    sql = """
    SET NAMES utf8;
    DROP DATABASE IF EXISTS %s;
    DROP USER %s@localhost;
    """ % (
        settings.DATABASE_NAME,
        settings.DATABASE_USER,
    )
    print sql
    proc = subprocess.Popen(['mysql', '--user', 'root', '--password=%s' % password], stdin=subprocess.PIPE)
    proc.communicate(sql + '\n')
    
    # Create the DB & user
    print 'Creating database %s' % settings.DATABASE_NAME
    sql = """
    SET NAMES utf8;
    -- Create the DB, create user, grant all DB privileges to user
    CREATE DATABASE %s CHARACTER SET utf8 COLLATE utf8_unicode_ci;
    CREATE USER %s@localhost IDENTIFIED BY '%s';
    GRANT ALL ON %s.* TO %s@localhost;
    """ % (
        settings.DATABASE_NAME,
        settings.DATABASE_USER,
        settings.DATABASE_PASSWORD,
        settings.DATABASE_NAME,
        settings.DATABASE_USER,
    )
    print sql
    proc = subprocess.Popen(['mysql', '--user', 'root', '--password=%s' % password], stdin=subprocess.PIPE)
    proc.communicate(sql + '\n')

def create_migrations():
    import re
    for appname in settings.INSTALLED_APPS:
        if app_name not in ['noomake', 'ieeetags.site_admin']:
            base_appname = re.sub('^.+\\.', '', appname)
            os.system('python manage.py dmigration app %s' % base_appname)

def drop_all_tables():
    MAX_ITERATIONS = 15
    
    count = 0
    table_names = [1]
    
    # Loop through and keep dropping tables until there are none left (due to foreign key constraints, some tables wont drop the first time around)
    while len(table_names) > 0 and count < MAX_ITERATIONS:
        cmd = 'SHOW TABLES;'
        result = _run_mysql_cmd(cmd)
        print 'result:', result
        table_names = result.strip().split('\n')
        del table_names[0]

        drop_cmd = ''
        print 'There are %d tables' % len(table_names)
        for table_name in table_names:
            print 'Dropping table %s' % table_name
            drop_cmd = 'DROP TABLE %s;\n' % table_name
            _run_mysql_cmd(drop_cmd)
        
        count += 1

    cmd = 'SHOW TABLES;'
    result = _run_mysql_cmd(cmd).strip()
    
    if result != '':
        print 'Tables remaining:'
        print result

def dump():
    import subprocess
    import settings
    args = [
        'mysqldump',
        '--user=%s' % settings.DATABASE_USER,
        '--password=%s' % settings.DATABASE_PASSWORD,
        '%s' % settings.DATABASE_NAME,
    ]
    subprocess.call(args)

def load():
    import os
    os.system('python manage.py dbshell')

def mig():
    import os
    os.system('python manage.py dmigrate all')

def reset():
    #create_db()
    drop_all_tables()
    mig()
    os.system('manage.py loaddata initial_data')

#def sync():
#    import os
#    os.system('python manage.py syncdb')

def main():
    opts, args = getopt(sys.argv[1:], '', [])
    if len(args) == 0:
        print 'Usage:'
        print '  create_db - create the DB using the mysql command line (needs mysql root password)'
        print '  create_migrations - create a migration for every app (bootstrap)'
        print '  drop_all_tables - drop all db tables'
        print '  dump - dump DB using mysqldump'
        print '  load - shortcut to dbshell, use with < to load sql data'
        print '  mig - shortcut to "dmigrate all"'
        print '  reset - drops tables & recreates'
        #print '  sync - shortcut to "syncdb"'
        sys.exit()
    
    #FUNCTIONS = [
    #    'create_db',
    #    'create_migrations',
    #    'drop_all_tables',
    #    'dump',
    #    'load',
    #    'mig',
    #    'reset',
    #    'sync',
    #]
    
    for arg in args:
        if arg == 'create_db':
            create_db()
        elif arg == 'create_migrations':
            create_migrations()
        elif arg == 'drop_all_tables':
            drop_all_tables()
        elif arg == 'dump':
            dump()
        elif arg == 'load':
            load()
        elif arg == 'mig':
            mig()
        elif arg == 'reset':
            reset()
        #elif arg == 'sync':
        #    sync()
        else:
            print 'Unrecognized arg "%s"' % arg
            sys.exit()

if __name__ == '__main__':
    main()