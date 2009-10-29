from django import template
from logging import debug as log

register = template.Library()

@register.filter
def textlist(values):
    """
    Turns a list of values into a textual list.
    ie. [1] becomes "1"
    ie. [1, 2] becomes "1 and 2"
    ie. [1, 2, 3] becomes "1, 2, and 3"
    """
    
    list1 = [str(value) for value in values]
    
    if len(list1) == 0:
        return ''
    else:
        str1 = ''
        for i in range(len(list1) - 1):
            if i > 0:
                str1 += ', '
            str1 += list1[i]
        
        if len(list1) == 1:
            str1 += '%s' % list1[len(list1)-1]
        elif len(list1) == 2:
            str1 += ' and %s' % list1[len(list1)-1]
        elif len(list1) > 2:
            str1 += ', and %s' % list1[len(list1)-1]
            
        return str1

@register.filter
def truncatechars(value, arg):
    'Like truncatewords, except it works by char count.'
    char_count = int(arg)
    if len(value) > char_count:
        return value[:char_count] + '...'
    else:
        return value
