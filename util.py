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

def profiler(filename=None):
    def _outter(func):
        print '_outter()'
        
        def _inner(*args, **kwargs):
            try:
                # For Python 2.5:
                import cProfile as profile
            except ImportError:
                # For Python 2.4:
                import profile
                
            import settings
            import time
            
            # NOTE: Must use this, or the 'filename' global/local var gets messed up.
            filename2 = filename
            
            print '_inner()'
            
            if filename2 is None:
                # Default to <function_name>_<time>.txt and .out
                filename2 = '%s_%s' % (func.__name__, time.time())
                
            filename_full = os.path.join(settings.PROFILER_OUTPUT_ROOT, filename2)
            print 'filename2: %r' %filename2
            print 'filename_full: %r' %filename_full
                
            if settings.PROFILER_OUTPUT_ROOT is None:
                raise Exception('settings.PROFILER_OUTPUT_ROOT must be set to save profiler output.')
            elif not os.path.exists(settings.PROFILER_OUTPUT_ROOT):
                raise Exception('The settings.PROFILER_OUTPUT_ROOT folder %r does not exist.' % settings.PROFILER_OUTPUT_ROOT)
            
            #print '  func: %r' % func
            #print '  args: %s' % repr(args)
            #print '  kwargs: %s' % repr(kwargs)
            #print '  ----------'
            #result = func(*args, **kwargs)
            prof = profile.Profile()
            result = prof.runcall(func, *args, **kwargs )
            print 'result: %r' % result
            
            #prof.print_stats()
            
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
            
            # Save the binary output.
            prof.dump_stats(filename_full + '.profile_out')
            
            # Save kcachegrind-compatible output.
            if hasattr(prof, 'getstats'):
                import lsprofcalltree
                k = lsprofcalltree.KCacheGrind(prof)
                file1 = open(filename_full + '.kcachegrind', 'w')
                k.output(file1)
                del file1
            
            #print '  ----------'
            #print '~_inner()'
            return result
        return _inner
    return _outter

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
