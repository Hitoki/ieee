'''
This file checks all javascript files in the /meda/js folder for common typos.
For the moment, it only checks for this typo:
    {
        one: 1,
        two: 2,
    }
Note the extra trailing comma after "2" that will cause an error in IE.
'''

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core import util

jsdir = util.relpath(__file__, r'..\media\js')

