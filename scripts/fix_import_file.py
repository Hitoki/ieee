
# Setup django so we can run this from command-line

from django.core.management import setup_environ
import sys
sys.path = ['../..'] + sys.path
sys.path = ['..'] + sys.path
import ieeetags.settings
setup_environ(ieeetags.settings)

# --

from django.contrib.auth.models import User
from ieeetags.models import *
from ieeetags.site_admin.views import _open_unicode_csv_reader, _open_unicode_csv_writer
from logging import debug as log
import re
import time
import os

import csv
import cStringIO
import codecs

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        try:
            self.writer.writerow([s.encode("utf-8") for s in row])
        except Exception, e:
            print 'Writing row %r' % row
            temp = 0
            for col in row:
                print '  col %s: %r' % (temp, col)
                temp += 1
            raise
            
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def translate_old_society_abbr(abbr):
    ABBR_TABLE = {
        'ASC': 'CSC',
        'BIO': 'BMC',
        'CIS': 'CI',
        'CRFID': 'RFID',
        'EM': 'TMC',
        'IA': 'IAS',
        'LEO': 'PHOT',
        'PES': 'PE',
        'PSES': 'PSE',
        'PHO': 'PHOT',
        'SIT': 'SSIT',
        'SYSC': 'SYS',
    }
    
    if abbr in ABBR_TABLE:
        return ABBR_TABLE[abbr]
    else:
        return abbr

def main():
    
    filename = os.path.join(os.path.dirname(__file__), 'conferences.csv')
    out_filename1 = os.path.join(os.path.dirname(__file__), 'conferences-existing-project-codes.csv')
    out_filename2 = os.path.join(os.path.dirname(__file__), 'conferences-new.csv')
    
    file1, reader = _open_unicode_csv_reader(filename)
    out_file1, existing_writer = _open_unicode_csv_writer(out_filename1)
    #out_file2, new_writer = _open_unicode_csv_writer(out_filename2)
    new_writer = UnicodeWriter(open(out_filename2, 'wb'))
    
    existing_writer.writerow([
        'ieee_id',
        'project_code',
    ])

    new_writer.writerow([
        'Type',
        'ID',
        'Name',
        'Description',
        'URL',
        'Tags',
        'Society Abbreviations',
        #'NEW Society Abbreviations !!!',
        'Conference Year',
        'Standard Status',
        'Standard Technical Committees',
        'Keywords',
        'Priority',
        'Completed',
        'Project Code',
        'Date',
    ])

    error_societies = set()
    errors = []
    
    num_resources = 0
    
    num_resources_pre_1996 = 0
    
    num_new_resources = 0
    num_new_resource_blank_society = 0
    num_new_resource_bad_society_abbr = 0
    num_new_resource_no_society_matches = 0
    
    num_existing_resources = 0
    num_existing_resources_project_code = 0
    num_existing_resources_no_project_code = 0
    
    start = time.time()
    
    # Defaults for missing columns
    type1 = ''
    ieee_id = ''
    name = ''
    description = ''
    url = ''
    tag_names = ''
    society_abbreviations = ''
    new_society_abbreviations = ''
    conference_year = ''
    standard_status = ''
    standard_technical_committees = ''
    keywords = ''
    priority_to_tag = ''
    completed = ''
    project_code = ''
    date1 = ''
    
    conference_type = ResourceType.objects.getFromName(ResourceType.CONFERENCE)

    try:
        for row in reader:
            
            #Type, ID, Name, Description, URL, Tags, Society Abbreviations, Conference Year, Standard Status, Standard Technical Committees, Keywords, Priority, Completed, Project Code, Date
            
            #print 'row: %r' % row
            #for col in row:
            #   print '  col: %r' % col
            
            
            # Modified input file:
            #Type,ID,name,description,url,Tags,Society Abbreviations,Conference Year,Priority,Completed,Project Code
            type1, ieee_id, name, description, url, tag_names, society_abbreviations, conference_year, priority_to_tag, completed, project_code = row
            
            #print 'ieee_id: %s' % ieee_id
            #log('  society_abbreviations: %r' % society_abbreviations)
            
            #log('conference_year: %s' % conference_year)
            #log('int(conference_year): %s' % int(conference_year))
            
            # Defaults
            priority_to_tag = 'no'
            completed = 'no'
            
            if int(conference_year) < 1996:
                # Ignore all resources before 1996
                #assert False, 'Resource is before 1996'
                num_resources_pre_1996 += 1
                
            else:
                
                resources = Resource.objects.filter(ieee_id=ieee_id, resource_type=conference_type)
                #print 'Found %s resources.' % resources.count()
                
                assert resources.count() >= 0 and resources.count() <= 1
                
                if resources.count() > 0:
                    # Found an existing resource
                    resource = resources[0]
                    #print 'Existing Resource'
                    #print '  old conference_series: %s' % resource.conference_series
                    #print '  new project_code:      %s' % project_code
                    
                    if project_code.strip() == '':
                        errors.append('New project_code for %s is empty.' % ieee_id)
                        num_existing_resources_no_project_code += 1
                    else:
                        # Update the conference_series only
                        #print '  Updating conference_series.'
                        num_existing_resources_project_code += 1
                    
                    existing_writer.writerow([
                        ieee_id,
                        project_code.strip(),
                    ])
                    
                    num_existing_resources += 1
                    
                else:
                    # New Resource
                    
                    societies = []
                    
                    if society_abbreviations == '':
                        #print 'society abbreviation is blank, skipping'
                        num_new_resource_blank_society += 1
                    else:
                        
                        matches = re.finditer(r' - ([A-Z]+)\b', society_abbreviations)
                        #print '  matches: %r' % matches
                        
                        num_matches = 0
                        
                        for match in matches:
                            num_matches += 1
                            
                            abbr = match.group(1)
                            #print '  abbr: %s' % abbr
                            
                            abbr = translate_old_society_abbr(abbr)
                            #print '  translated abbr: %s' % abbr
                            
                            society = Society.objects.getFromAbbreviation(abbr)
                            #print '  society: %r' % society
                            
                            if society is None:
                                error = 'No society for %r (%r)' % (abbr, society_abbreviations)
                                print error
                                #assert False
                                error_societies.add(abbr)
                                errors.append(error)
                                num_new_resource_bad_society_abbr += 1
                            else:
                                societies.append(society)
                        
                        if num_matches == 0:
                            error = 'There were no matches for resource %s, society_abbreviations %r' % (ieee_id, society_abbreviations)
                            #print error
                            errors.append(error)
                            num_new_resource_no_society_matches += 1
                    
                    new_society_abbreviations = '|'.join([society.abbreviation for society in societies])
                    
                    try:
                        new_writer.writerow([
                            type1,
                            ieee_id,
                            name,
                            description,
                            url,
                            tag_names,
                            #society_abbreviations,
                            new_society_abbreviations,
                            conference_year,
                            standard_status,
                            standard_technical_committees,
                            keywords,
                            priority_to_tag,
                            completed,
                            project_code,
                            date1,
                        ])
                    except UnicodeEncodeError, e:
                        log('Got UnicodeEncodeError exception.')
                        log('  type1: %r' % type1)
                        log('  ieee_id: %r' % ieee_id)
                        log('  name: %r' % name)
                        log('  description: %r' % description)
                        log('  url: %r' % url)
                        log('  tag_names: %r' % tag_names)
                        log('  new_society_abbreviations: %r' % new_society_abbreviations)
                        log('  conference_year: %r' % conference_year)
                        log('  standard_status: %r' % standard_status)
                        log('  standard_technical_committees: %r' % standard_technical_committees)
                        log('  keywords: %r' % keywords)
                        log('  priority_to_tag: %r' % priority_to_tag)
                        log('  completed: %r' % completed)
                        log('  project_code: %r' % project_code)
                        log('  date1: %r' % date1)
                        raise
                    
                    num_new_resources += 1
            
            num_resources += 1
            
            #if num_resources > 100:
            #    break
            
            if not (num_resources % 100):
                elapsed = time.time() - start
                if elapsed != 0:
                    print '#%s, %s/s' % (num_resources, num_resources/elapsed)
    
    except UnicodeDecodeError, e:
        log('Got UnicodeDecodeError exception.  The data for the *previous* row:')
        log('  type1: %r' % type1)
        log('  ieee_id: %r' % ieee_id)
        log('  name: %r' % name)
        log('  description: %r' % description)
        log('  url: %r' % url)
        log('  tag_names: %r' % tag_names)
        log('  new_society_abbreviations: %r' % new_society_abbreviations)
        log('  conference_year: %r' % conference_year)
        log('  standard_status: %r' % standard_status)
        log('  standard_technical_committees: %r' % standard_technical_committees)
        log('  keywords: %r' % keywords)
        log('  priority_to_tag: %r' % priority_to_tag)
        log('  completed: %r' % completed)
        log('  project_code: %r' % project_code)
        log('  date1: %r' % date1)
        raise

    print ''
    print 'num_resources: %s' % num_resources
    print 'num_new_resources: %s' % num_new_resources
    print 'num_new_resource_blank_society: %s' % num_new_resource_blank_society
    print 'num_new_resource_bad_society_abbr: %s' % num_new_resource_bad_society_abbr
    print 'num_new_resource_no_society_matches: %s' % num_new_resource_no_society_matches
    
    print 'num_existing_resources: %s' % num_existing_resources
    print 'num_existing_resources_project_code: %s' % num_existing_resources_project_code
    print 'num_existing_resources_no_project_code: %s' % num_existing_resources_no_project_code
    
    
    print ''
    print 'Bad Societies Columns:'
    print ''
    for soc in error_societies:
        print soc
    
    #print ''
    #print 'Errors:'
    #print ''
    #for error in errors:
    #    print error

if __name__ == '__main__':
    main()

