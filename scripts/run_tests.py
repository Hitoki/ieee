'''
Runs the "manage.py test" command, captures the output, emails the results (pass/fail) to the admins.
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

from ieeetags.util import send_admin_email, get_svn_info, relpath

def main():
    import re
    
    svn_info = get_svn_info(relpath(__file__, '..'))
    revision = svn_info['revision']
    
    # Run the django 'test' command, capture the output.
    
    import subprocess
    proc = subprocess.Popen([sys.executable, relpath(__file__, '../manage.py'), 'test'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err_output = proc.communicate()
    
    # Parse the results to see if there was an error.
    
    success_matches = re.search(r'Ran (\d+) tests in (\d\.\d+)s\n\nOK', err_output)
    
    if success_matches:
        # No errors.
        subject = 'Tests passed for rev %s.' % revision
        body = subject
    else:
        # Found errors.
        matches = re.search(r'FAILED \(failures=(\d+)\)', err_output)
        if matches:
            num_errors = matches.group(1)
        else:
            num_errors = '(Unknown)'
        subject = '*** Tests failed for rev %s, %s errors.' % (revision, num_errors)
        body = err_output
    
    print subject
    print body
    
    send_admin_email(subject, body)
    
if __name__ == '__main__':
    main()
    