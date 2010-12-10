import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from getopt import getopt
import settings
import subprocess

def main():
    
    opts, args = getopt(sys.argv[1:], 'dc', ['drop', 'create'])
    
    do_drop = False
    do_create = False
    
    for name, value in opts:
        if name == '--drop' or name == '-d':
            do_drop = True
        if name == '--create' or name == '-c':
            do_create = True
    
    if not do_drop and not do_create:
        do_drop = True
        do_create = True
        #print 'Must specify --drop or --create.'
        #exit()
    
    sql = ''
    
    if do_drop:
        print 'Dropping database %s' % settings.DATABASE_NAME
        sql += """
        SET NAMES utf8;
        DROP DATABASE IF EXISTS %s;
        DROP USER %s@localhost;
        """ % (
            settings.DATABASE_NAME,
            settings.DATABASE_USER,
        )
    
    if do_create:
        print 'Creating database %s' % settings.DATABASE_NAME
        sql += """
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

    proc = subprocess.Popen(['mysql', '-u', 'root', '-p'], stdin=subprocess.PIPE)
    proc.communicate(sql + '\n')

if __name__ == '__main__':
    main()