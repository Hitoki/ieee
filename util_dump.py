import subprocess
import settings
args = [
    'mysqldump',
    '--user=%s' % settings.DATABASE_USER,
    '--password=%s' % settings.DATABASE_PASSWORD,
    '%s' % settings.DATABASE_NAME,
]
subprocess.call(args)
