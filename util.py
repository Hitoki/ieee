#!/usr/bin/python

import os.path
import time


# Django util functions -------------------------------------------------------


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
        #file.seek(-1, os.SEEK_CUR)

        # NOTE: This is for Python 2.4 compatability
        SEEK_CUR = 1
        file.seek(-1, SEEK_CUR)
        return False


def begins_with(str1, prefix):
    """
    DEPRECATED: This should be replaced with x.beginswith(...) instead.
    """
    return str1[:len(prefix)] == prefix


class EndUserException(Exception):
    pass


def default_date_format(date1=None):
    """
    Formats a date.
    """
    import datetime
    if date1 is None:
        date1 = datetime.date.today()
    return date1.strftime('%a %b %d, %Y')


def default_time_format(time1=None):
    """
    Formats a time.
    """
    import time
    if time1 is None:
        time1 = time.localtime()
    return time.strftime('%I:%M %p', time1)


def default_datetime_format(datetime1=None):
    """
    Formats a date/time.
    """
    return default_date_format(datetime1) + ' ' + default_time_format(datetime1)


def generate_password(length=8, chars='all'):
    """
    Creates a random string useful for passwords.
    @param length: The number of chars for this password.
    @param chars: The charset to use, can be ALPHA_LOWER, ALPHA_UPPER, ALPHA,
    NUMERIC, SYMBOLS, SYMBOLS2, or ALL.
    """
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
    elif chars == 'alpha':
        CHARS = ALPHA
    elif chars == 'numeric':
        CHARS = NUMERIC
    elif chars == 'loweralpha':
        CHARS = ALPHA_LOWER
    elif chars == 'loweralphanumeric':
        CHARS = ALPHA_LOWER + NUMERIC
    elif chars == 'upperalpha':
        CHARS = ALPHA_UPPER
    elif chars == 'upperalphanumeric':
        CHARS = ALPHA_UPPER + NUMERIC
    else:
        raise Exception('Unknown chars "%s"' % chars)

    passwd = ''
    for i in range(length):
        passwd += random.choice(CHARS)
    return passwd


def generate_words(min, max, chars='loweralpha'):
    """
    Generates random strings of chars, for testing.
    """
    import random
    length = random.randint(min, max)
    string = generate_password(length, chars)
    i = 0
    while i < len(string):
        i += random.randint(2, 10)
        string = string[:i] + ' ' + string[i:]
    return string

from UserDict import UserDict


class odict(UserDict):
    """
    Represents an ordered dict.  Normal dict objects do not maintain order.
    """
    def __init__(self, dict=None):
        self._keys = []
        UserDict.__init__(self, dict)

    def __delitem__(self, key):
        UserDict.__delitem__(self, key)
        self._keys.remove(key)

    def __setitem__(self, key, item):
        UserDict.__setitem__(self, key, item)
        if key not in self._keys:
            self._keys.append(key)

    def clear(self):
        UserDict.clear(self)
        self._keys = []

    def copy(self):
        dict = UserDict.copy(self)
        dict._keys = self._keys[:]
        return dict

    def items(self):
        return zip(self._keys, self.values())

    def keys(self):
        return self._keys

    def popitem(self):
        try:
            key = self._keys[-1]
        except IndexError:
            raise KeyError('dictionary is empty')

        val = self[key]
        del self[key]

        return (key, val)

    def setdefault(self, key, failobj=None):
        UserDict.setdefault(self, key, failobj)
        if key not in self._keys:
            self._keys.append(key)

    def update(self, dict):
        UserDict.update(self, dict)
        for key in dict.keys():
            if key not in self._keys:
                self._keys.append(key)

    def values(self):
        return map(self.get, self._keys)


def group_conferences_by_series(resources, include_current_conference=False):
    """
    For a sequence of resources, groups any conferences in the same series
    together.
        -Loop through each conference series
        -If the
    """
    resources = list(resources)

    # Create a dict of series with all matching conferences from the list.
    series_conferences = {}
    for resource in resources:
        if resource.conference_series != '':
            if resource.conference_series not in series_conferences:
                series_conferences[resource.conference_series] = []
            series_conferences[resource.conference_series].append(resource)

    # Loop through all conferences in each series, remove them from the main
    # list unless they're the current conference.
    for series, conferences in series_conferences.items():
        import datetime

        # Find the most recent conference for each series
        current_year = datetime.datetime.now().year
        conferences.sort(key=lambda obj: obj.year)

        # Choose the next future conference
        current_conference = None
        for conference in conferences:
            if conference.year >= current_year:
                current_conference = conference
                break

        if current_conference is None:
            # Choose the most recent past conference (if there are any)
            if len(conferences) > 0:
                current_conference = conferences[len(conferences)-1]

        assert current_conference is not None

        i = 0
        while i < len(resources):
            if resources[i] == current_conference:
                # Found the current conference in a series

                resources[i].is_current_conference = True
                other_conferences = \
                    series_conferences[resources[i].conference_series]

                if not include_current_conference:
                    other_conferences1 = []
                    for conference in other_conferences:
                        if conference != current_conference:
                            other_conferences1.append(conference)
                    other_conferences = other_conferences1

                # Sort the other conferences by year latest to earliest.
                other_conferences = \
                    sorted(other_conferences,
                           key=lambda resource: resource.year, reverse=True)

                resources[i].other_conferences = other_conferences
                i += 1
            elif resources[i] in conferences:
                # Remove all the non-current conferences
                # warning: altering collection while looping through it.
                del resources[i]
            else:
                # Found a non-series resource, just ignore it
                i += 1
    return resources


def word_wrap(string, max_chars):
    """
    Breaks up a string into separate lines, wrapping at word boundaries.
    """
    import re

    lines = [string]

    # Loop while the latest line has more than max_chars chars...
    while len(lines[len(lines)-1]) > max_chars:
        index = len(lines)-1
        expr = re.compile(r'\b')
        rline = lines[index][::-1]
        start_pos = len(lines[index]) - 20
        match = expr.search(rline, start_pos)
        if match is not None:
            pos = len(lines[index]) - match.start()
            line = lines[index]
            lines[index] = line[:pos]
            lines.append(line[pos:])

    result = '\n'.join(lines)
    return result


def profiler(view_func):
    """
    Decorator to use for profiling a specific view.  Use like:
        @profiler
        def your_view(request):
            ...
    Will output profiler data files to the folder set in
    settings.PROFILER_OUTPUT_ROOT.
    By default, filename is [function_name] + [time].
    Outputs 3 formats:
        .txt - printed stats summary.
        .profile_out - binary python profiler output.
        .kcachegrind - kchachegrind-compatible output.
    """
    #print 'profiler()'
    def _inner(*args, **kwargs):
        try:
            # For Python 2.5+:
            import cProfile as profile
        except ImportError:
            # For Python 2.4:
            import profile

        import settings
        import sys

        # NOTE: Must use this, or the 'filename' global/local var gets
        # messed up.
        #filename2 = filename
        filename2 = None

        #print '_inner()'

        if filename2 is None:
            # Default to <function_name>_<time>.txt and .out
            filename2 = '%s_%s' % (view_func.__name__, time.time())

        filename_full = os.path.join(settings.PROFILER_OUTPUT_ROOT, filename2)
        #print 'filename2: %r' %filename2
        #print 'filename_full: %r' %filename_full

        if settings.PROFILER_OUTPUT_ROOT is None:
            raise Exception('settings.PROFILER_OUTPUT_ROOT must be set '
                            'to save profiler output.')
        elif not os.path.exists(settings.PROFILER_OUTPUT_ROOT):
            os.mkdir(settings.PROFILER_OUTPUT_ROOT)
            # raise Exception('The settings.PROFILER_OUTPUT_ROOT folder %r '
            #                'does not exist.' % settings.PROFILER_OUTPUT_ROOT)

        #print '  view_func: %r' % view_func
        #print '  args: %s' % repr(args)
        #print '  kwargs: %s' % repr(kwargs)
        #print '  ----------'
        #response = view_func(*args, **kwargs)

        if settings.PROFILER_OUTPUT_LINEBYLINE:
            import line_profiler
            prof = line_profiler.LineProfiler(view_func)

            response = prof.runcall(view_func, *args, **kwargs)
            #print 'response: %r' % response

            # Line-by-line profiler
            file1 = open(filename_full + '.lineprofiler.txt', 'w')

            #prof.print_stats(file1)

            stats = prof.get_stats()
            #line_profiler.show_text(stats.timings, stats.unit, stream=file1)

            def show_text2(stats, unit, stream=None):
                """ Show text for the given timings.
                """
                if stream is None:
                    stream = sys.stdout
                #print >>stream, 'Timer unit: %g s' % unit
                #print >>stream, ''
                for (fn, lineno, name), timings in sorted(stats.items()):
                    show_func2(fn, lineno, name, stats[fn, lineno, name], unit,
                               stream=stream)

            def show_func2(filename, start_lineno, func_name, timings, unit,
                           stream=None):
                """ Show results for a single function.
                """
                from line_profiler import linecache, inspect

                if stream is None:
                    stream = sys.stdout
                print >>stream, "File: %s" % filename
                print >>stream, "Function: %s at line %s" % (func_name,
                                                             start_lineno)
                template = '%6s %9s %12s %8s %8s  %-s'
                d = {}
                total_time = 0.0
                linenos = []
                for lineno, nhits, time in timings:
                    total_time += time
                    linenos.append(lineno)
                print >>stream, "Total time: %g s" % (total_time * unit)
                if not os.path.exists(filename):
                    print >>stream, ""
                    print >>stream, "Could not find file %s" % filename
                    print >>stream, "Are you sure you are running this " \
                                    "program from the same directory"
                    print >>stream, "that you ran the profiler from?"
                    print >>stream, "Continuing without the function's " \
                                    "contents."
                    # Fake empty lines so we can see the timings,
                    # if not the code.
                    nlines = max(linenos) - min(min(linenos), start_lineno) + 1
                    sublines = [''] * nlines
                else:
                    all_lines = linecache.getlines(filename)
                    sublines = inspect.getblock(all_lines[start_lineno-1:])
                for lineno, nhits, time in timings:
                    d[lineno] = (nhits, time, '%5.1f' % (float(time) / nhits),
                        '%5.1f' % (100*time / total_time))
                linenos = range(start_lineno, start_lineno + len(sublines))
                empty = ('', '', '', '')
                header = template % ('Line #', 'Hits', 'Time', 'Per Hit',
                                     '% Time', 'Line Contents')
                print >>stream, ""
                print >>stream, header
                print >>stream, '=' * len(header)

                for lineno, line in zip(linenos, sublines):
                    nhits, time, per_hit, percent = d.get(lineno, empty)

                    if per_hit != '':
                        per_hit = round(float(per_hit) * unit, 2)
                        if per_hit == 0:
                            per_hit = '-'
                        else:
                            per_hit = '%0.2f' % per_hit

                    if time != '':
                        time = round(float(time) * unit, 2)
                        if time == 0:
                            time = '-'
                        else:
                            time = '%0.2f' % time

                    if percent != '' and float(percent) == 0:
                        percent = '-'

                    print >>stream, template % \
                                    (lineno, nhits, time, per_hit, percent,
                                     line.rstrip('\n').rstrip('\r'))
                print >>stream, ""

            show_text2(stats.timings, stats.unit, stream=file1)

            del file1

        else:

            # Other (not line-by-line) profilers.

            prof = profile.Profile()

            response = prof.runcall(view_func, *args, **kwargs)
            #print 'response: %r' % response

            if hasattr(settings, 'PROFILER_OUTPUT_TXT') \
                    and settings.PROFILER_OUTPUT_TXT:
                # Save text output.
                file1 = open(filename_full + '.txt', 'w')
                old_stdout = sys.stdout
                sys.stdout = file1
                # Internal Time
                #prof.print_stats(sort=1)
                # Cumulative
                prof.print_stats(sort=2)
                sys.stdout = old_stdout
                del file1

            if (hasattr(settings, 'PROFILER_OUTPUT_BINARY')
                    and settings.PROFILER_OUTPUT_BINARY) \
                    or (hasattr(settings, 'PROFILER_OUTPUT_PNG')
                        and settings.PROFILER_OUTPUT_PNG):
                # Save the binary output.
                prof.dump_stats(filename_full + '.profile_out')

                if hasattr(settings, 'PROFILER_OUTPUT_PNG') \
                        and settings.PROFILER_OUTPUT_PNG:
                    # Create the PNG callgraph image.
                    os.system('%s -f pstats %s | dot -Tpng -o %s 2>NUL' %
                              (relpath(__file__, 'scripts/gprof2dot.py'),
                               filename_full + '.profile_out',
                               filename_full + '.png'))

                if not hasattr(settings, 'PROFILER_OUTPUT_BINARY') \
                        or not settings.PROFILER_OUTPUT_BINARY:
                    # We only wanted the PNG file, delete the binary file now
                    # that we're done with it.
                    os.remove(filename_full + '.profile_out')

            if hasattr(settings, 'PROFILER_OUTPUT_KCACHEGRIND') \
                    and settings.PROFILER_OUTPUT_KCACHEGRIND:
                # Save kcachegrind-compatible output.
                if hasattr(prof, 'getstats'):
                    import lsprofcalltree
                    k = lsprofcalltree.KCacheGrind(prof)
                    file1 = open(filename_full + '.kcachegrind', 'w')
                    k.output(file1)
                    del file1

        #print '  ----------'
        #print '~_inner()'
        return response
    return _inner


def truncate_link_list(items, output_func, plain_output_func, max_chars,
                       tag=None, tab_name=None):
    """
    Takes a list of items and outputs links.  If the list is > max_chars,
    the list is truncated with '...(10 more)' appended.
    @param items: the list of items
    @param output_func: the HTML output formatting function, takes one item
    as its argument
    @param output_func: the Plaintext output formatting function, takes one
    item as its argument.  This is used to determine the content length
    (w/o HTML markup tags)
    @param max_chars: the maximum length of the output, not including
    the '... (X more)' if necessary
    """
    #print 'truncate_link_list()'
    #print '  tag: %r' % tag
    items_str = ''
    items_plaintext = ''

    for i in range(len(items)):
        item = items[i]
        if items_str != '':
            items_plaintext += ', '

        str1 = output_func(item)
        items_plaintext += plain_output_func(item)

        if len(items_plaintext) > max_chars:
            # check if tab_name exists as to not mess up clusters
            if tab_name is None:
                items_str += ' ... (%s more)' % (len(items) - i)
            else:
                if tag is not None:
                    items_str += ' ... (%s more - <a href="javascript:Tags.selectTag(%s, &quot;%s&quot;);">show all</a>)' % (len(items) - i, tag.id, tab_name)
                else:
                    items_str += ' ... (%s more)' % (len(items) - i)
            break
        else:
            if items_str != '':
                items_str += ', '
            items_str += str1

    return items_str


def get_min_max(list, attr):
    """
    Finds the min and max value of the attr attribute of each item in the list.
    @param list: the list of items.
    @param attr: the name of the attribute to check the value.
    @return: A 2-tuple (min, max).
    """
    min1 = None
    max1 = None
    for item in list:
        if min1 is None or getattr(item, attr) < min1:
            min1 = getattr(item, attr)
        if max1 is None or getattr(item, attr) > max1:
            max1 = getattr(item, attr)
    return (min1, max1)


def send_admin_email(subject, body):
    """
    Sends an email to the admins.
    """
    import settings
    from django.core.mail import send_mail

    emails = [temp[1] for temp in settings.ADMINS]
    try:
        send_mail(subject, body, settings.SERVER_EMAIL, emails)
    except Exception, e:
        # Silent fail.
        print 'Error while sending email:'
        print e
        #raise
        pass


def make_choices(values):
    for value in values:
        yield (str(value), str(value))


def get_process_info(pid):
    """
    Returns the command line for a given PID.
    Returns None if the process does not exist.
    """
    import subprocess
    proc = subprocess.Popen(['ps', 'p', str(pid), 'h', '-o', 'args'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if err != '':
        raise Exception('Error while calling "ps" command: %s' % err)
    if out == '':
        return None
    return out.strip()


def safejoin(a, b):
    """
    Works like os.path.join(a, b) - but insures that the result is within
    the "a" folder.
    """
    import os
    #print 'safejoin()'
    #print '  a: %r' % a
    a = os.path.abspath(a)
    if a[-1:] != os.sep:
        a += os.sep
    #print '  a: %r' % a
    #print '  b: %r' % b
    c = os.path.abspath(os.path.join(a, b))

    if len(c) < len(a):
        # Special case - c is a directory, but does not yet end with /
        if c[-1:] != os.sep:
            c += os.sep
    #print '  c: %r' % c
    if c[:len(a)] != a:
        raise Exception('Resulting path %r is not within parent path %r' %
                        (c, a))
    return os.path.abspath(c)


def update_conference_series_tags(conferences=None, conference_series=None):
    """
    Updates conferences so that each future conference inherits all previous
    years' conferences' tags.
    Must give either conferences or conference_series.
    @param conferences A list of conferences to update, should be sorted
    by conference_series, then year.  All conferences should have a valid
    conference_series value, and a valid year value.
    @param conference_series (string) A series to parse through. Will grab all
    conferences of this series and update them.
    """
    from models.resource import Resource, ResourceNodes
    from models.types import ResourceType
    #from ieeetags.models import Resource, ResourceNodes, ResourceType
    #import models
    if conferences is not None and conference_series is None:
        pass
    elif conferences is None and conference_series is not None:
        conference_type = \
            ResourceType.objects.getFromName(ResourceType.CONFERENCE)
        conferences = \
            Resource.objects.filter(resource_type=conference_type,
                                    conference_series=conference_series).\
                order_by('year')
    else:
        raise Exception('Both conferences (%r) and conference_series (%r) '
                        'were specified, should only specify one.' %
                        (conferences, conference_series))

    num_conferences = 0
    num_series = 0
    num_tags_added = 0

    num_total_conferences = conferences.count()

    series = ''
    last_update_time = None
    start = time.time()
    for i, conference in enumerate(conferences):
        assert conference.conference_series.strip() != ''
        assert conference.year is not None
        assert conference.year != 0

        if series != conference.conference_series:
            # Start of a new series.
            tags = []
            series = conference.conference_series
            num_series += 1
            #print ''

        tags1 = [tag.name for tag in conference.nodes.all()]
        num_tags1 = conference.nodes.count()

        # Add all previous tags to this conference.
        for tag in tags:
            if tag not in conference.nodes.all():
                resource_nodes = ResourceNodes()

                #print 'conference: %r' % conference
                #print 'type(conference): %s' % type(conference)
                #print 'conference.name: %r' % conference.name
                #
                #print 'Resource: %r' % Resource
                #print 'models.Resource: %r' % models.Resource

                resource_nodes.resource = conference
                resource_nodes.node = tag
                resource_nodes.is_machine_generated = True
                resource_nodes.save()

        # Add all of this conference's tags to the list.
        for tag in conference.nodes.all():
            if tag not in tags:
                tags.append(tag)
                num_tags_added += 1
        conference.save()

        tags2 = [tag.name for tag in conference.nodes.all()]
        num_tags2 = conference.nodes.count()

        #print 'conference: %s, %s, %s, %s' % (conference.id, conference.conference_series, conference.year, conference.name)
        #print '  %s' % (','.join(tags1))
        #print '  %s' % (','.join(tags2))

        num_conferences += 1

        if not last_update_time or time.time() - last_update_time > 1:
            try:
                logging.debug('    Parsing row %d/%d, row/sec %f' %
                              (i, num_total_conferences, i/(time.time()-start)))
            except Exception:
                pass
            last_update_time = time.time()

    return {
        'num_conferences': num_conferences,
        'num_series': num_series,
        'num_tags_added': num_tags_added,
    }


def urldecode(query):
    import urllib
    data = {}
    pairs = query.split('&')
    for pair in pairs:
        if pair.find('='):
            k, v = map(urllib.unquote, pair.split('='))
            if k in data:
                data[k].append(v)
            else:
                data[k] = [v]
    return data


def get_svn_info(path):
    import re
    import subprocess

    proc = subprocess.Popen(
        ['svn', 'info', path],
        #cwd=path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    stdout, temp = proc.communicate()

    result = {
        'url': None,
        'revision': None,
    }

    matches = re.search(r'(?m)^URL: (.+)$', stdout)
    if matches:
        result['url'] = matches.group(1).strip()

    matches = re.search(r'(?m)^Revision: (.+)$', stdout)
    if matches:
        result['revision'] = matches.group(1).strip()

    return result

# -----------------------------------------------------------------------------

# NOTE: Cannot remove these yet, since they're included by default into any
# file that does "from util import *".  Need to fix all those first.
import subprocess
import settings
from getopt import getopt
import settings
import subprocess
import sys


def main():
    #out = get_process_info(1)
    #print 'out: %r' % out
    #
    #out = get_process_info(100)
    #print 'out: %r' % out

    #print get_svn_info(relpath(__file__, '..'))
    print get_svn_info(relpath(__file__, '.'))


if __name__ == '__main__':
    main()
