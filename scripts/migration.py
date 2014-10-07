#!/usr/local/bin/python
'Shortcut script - creates a migration with the given name and applies it.'

PYTHON_BINARY = 'python'
APP_NAME = 'ieeetags'

# ------------------------------------------------------------------------------

import os
path = os.path.dirname(os.path.abspath(__file__))

parent_path = os.path.join(path, '..')

import sys
sys.path = [parent_path] + sys.path
from core import util

if len(sys.argv) < 2:
	print 'Must specify migration name.'
	sys.exit()

#name = raw_input('Migration name: ')
name = sys.argv[1]
print 'Using migration name %r' % name

os.system('cd %s && %s manage.py schemamigration %s %s --auto && %s manage.py migrate' % (parent_path, PYTHON_BINARY, APP_NAME, name, PYTHON_BINARY))
print ''
