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

@register.filter
def reprjs(value):
    'This outputs a python value in javascript-friendly format.'
    
    # None
    if value is None:
        return 'null'
    
    # Strings
    if isinstance(value, basestring):
        value = value.replace('"', '\\"')
        value = '"' + value + '"'
        return value
    
    # Boolean
    if type(value) is bool:
        if value:
            return 'true'
        else:
            return 'false'
    
    # Integers/Longs
    if type(value) is int or type(value) is long:
        return value
    
    # Floats/Doubles
    if type(value) is float:
        return value
    
    raise ValueError('Could not convert value %r (type %r) to javascript.' % (value, type(value)))
    
