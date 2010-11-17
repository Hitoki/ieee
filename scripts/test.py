'''
Runs automated tests against the codebase.

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

import util

def check_js_files(path):
    import os
    import fnmatch
    import re
    
    results = []
    
    jsfilenames = []
    for root, dirnames, filenames in os.walk(path):
        for filename in fnmatch.filter(filenames, '*.js'):
            filename = os.path.join(root, filename)
            jsfilenames.append(filename)
        for filename in fnmatch.filter(filenames, '*.html'):
            filename = os.path.join(root, filename)
            jsfilenames.append(filename)

    for filename in jsfilenames:
        file = open(filename, 'r')
        content = file.read()
        file.close()
        del file
        
        matches = re.finditer(r'(?m)^(.*),\s*}(.*)$', content)
        del content
        
        result = {
            'filename': filename,
            'errors': [],
        }
        
        for match in matches:
            result['errors'].append(match.group(0))
        
        if len(result['errors']):
            results.append(result)
    
    return results

def main():
    
    s = []
    results = []
        
    jsdir = util.relpath(__file__, r'..\media\js')
    results.extend(check_js_files(jsdir))
    
    htmldir = util.relpath(__file__, r'..\templates')
    results.extend(check_js_files(htmldir))
    
    if len(results):
        s.append('Found possible JS errors.')
        for result in results:
            s.append('  Filename: %s' % result['filename'])
            for i, error in enumerate(result['errors']):
                if len(result['errors']) > 1:
                    s.append('    Error #%s:' % (i+1))
                for line in error.split('\n'):
                    s.append('      > %s' % line)
    
    s = '\n'.join(s)
    # Print output.
    print s
    
    # Email output.
    util.send_admin_email('Test report', s)

if __name__ == '__main__':
    main()
