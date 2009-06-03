
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
    return str1[:len(prefix)] == prefix

def ends_with(str1, prefix):
    return str1[-len(prefix):] == prefix

#def current_server_url(request):
#    print 'current_server_url()'
#    for name, value in request.META.items():
#        print '  %sm: %s' % (name, value)

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

def generate_password(length=8, chars='all'):
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
    elif chars == 'loweralphanumeric':
        CHARS = ALPHA_LOWER + NUMERIC
    elif chars == 'upperalphanumeric':
        CHARS = ALPHA_UPPER + NUMERIC
    else:
        raise Exception('Unknown chars "%s"' % chars)
    
    passwd = ''
    for i in range(length):
        passwd += random.choice(CHARS)
    return passwd

## Generate a human readable 'random' password
## password  will be generated in the form 'word'+digits+'word' 
## eg.,nice137pass
## parameters: number of 'characters' , number of 'digits'
## Pradeep Kishore Gowda <pradeep at btbytes.com >
## License : GPL 
## Date : 2005.April.15
## Revision 1.2 
## ChangeLog: 
## 1.1 - fixed typos 
## 1.2 - renamed functions _apart & _npart to a_part & n_part as zope does not allow functions to 
## start with _
#
#def nicepass(alpha=6,numeric=2):
#    """
#    returns a human-readble password (say rol86din instead of 
#    a difficult to remember K8Yn9muL ) 
#    """
#    import string
#    import random
#    vowels = ['a','e','i','o','u']
#    consonants = [a for a in string.ascii_lowercase if a not in vowels]
#    digits = string.digits
#    
#    ####utility functions
#    def a_part(slen):
#        ret = ''
#        for i in range(slen):			
#            if i%2 ==0:
#                randid = random.randint(0,20) #number of consonants
#                ret += consonants[randid]
#            else:
#                randid = random.randint(0,4) #number of vowels
#                ret += vowels[randid]
#        return ret
#    
#    def n_part(slen):
#        ret = ''
#        for i in range(slen):
#            randid = random.randint(0,9) #number of digits
#            ret += digits[randid]
#        return ret
#        
#    #### 	
#    fpl = alpha/2		
#    if alpha % 2 :
#        fpl = int(alpha/2) + 1 					
#    lpl = alpha - fpl	
#    
#    start = a_part(fpl)
#    mid = n_part(numeric)
#    end = a_part(lpl)
#    
#    return "%s%s%s" % (start,mid,end)
#    
##if __name__ == "__main__":
##    for i in range(30):
##        print nicepass(8,2)

from UserDict import UserDict

class odict(UserDict):
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
        exit()
    
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
            exit()

if __name__ == '__main__':
    main()