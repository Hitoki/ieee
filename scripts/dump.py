import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import subprocess
import settings
args = [
    'mysqldump',
    '--user=%s' % settings.DATABASE_USER,
    '--password=%s' % settings.DATABASE_PASSWORD,
    '%s' % settings.DATABASE_NAME,
]
subprocess.call(args)
