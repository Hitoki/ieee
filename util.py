
import os.path

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
        file.seek(-1, os.SEEK_CUR)
        return False

def begins_with(str1, prefix):
    return str1[:len(prefix)] == prefix

def ends_with(str1, prefix):
    return str1[-len(prefix):] == prefix

def current_server_url(request):
    #url = 
    print 'current_server_url()'
    for name, value in request.META.items():
        print '  %sm: %s' % (name, value)

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