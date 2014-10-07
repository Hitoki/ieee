'''
This file is meant to be run as a daemon.  It polls the SVN server every 60 seconds.  If a new revision is found, it updates the working copy and runs the "scripts/run_tests.py" file.
'''

# Setup django.
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import ieeetags.settings
from django.core.management import setup_environ
setup_environ(ieeetags.settings)

# ------------------------------------------------------------------------------

def main():
    from core.util import get_svn_info, relpath, send_admin_email
    import subprocess
    import time
    import getopt
    from cStringIO import StringIO
    
    log_filename = None
    
    opts, args = getopt.getopt(sys.argv[1:], 'l:')
    for name, value in opts:
        if name == '-l':
            log_filename = value
    
    if log_filename:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        #sys.stdout = StringIO()
        #sys.stderr = StringIO()
        
        sys.stdout = open(log_filename, 'a', 0)
        sys.stderr = sys.stdout
    
    print '----------------------------------------------------------------------'

    try:
        path = relpath(__file__, '..')
        
        url = svn_info = get_svn_info(path)['url']
        
        print 'Checking repo %s' % url
        
        # Run the first set of tests, regardless if the SVN is newer.
        print 'Running tests.'
        subprocess.call(
            [sys.executable, 'run_tests.py'],
        )
        
        while True:
            local_rev = get_svn_info(path)['revision']
            remote_rev = get_svn_info(url)['revision']
            
            if remote_rev is not None and local_rev != remote_rev:
                # The SVN is newer than the working-copy, update & test.
                print 'Updating working copy to latest revision.'
                print 'local_rev: %s' % local_rev
                print 'remote_rev: %s' % remote_rev
                
                #subject = 'Updating working copy from %s to %s' % (local_rev, remote_rev)
                #send_admin_email(subject, subject)
                
                subprocess.call(
                    ['svn', 'update', path],
                )
                
                print 'Running tests.'
                subprocess.call(
                    [sys.executable, 'run_tests.py'],
                )
                
                print '...'
            time.sleep(60)
    
    except KeyboardInterrupt:
        # Killed by keyboard.
        pass
        
    except Exception, e:
        print 'EXCEPTION: %r' % e
        subject = 'Test runner quit with exception %r' % e
        send_admin_email(subject, subject)
    
    if log_filename:
        f = sys.stdout
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        f.close()
    
if __name__ == '__main__':
    main()
