'''
This module handles threaded URL checking.
'''

import socket
import time
import threading
import urllib
import urlparse
from Queue import Empty, Queue
import datetime

from new_models.logs import UrlCheckerLog
from new_models.resource import Resource


class ArrayThreadSafe(object):
    def __init__(self):
        self.lock = threading.Condition(threading.Lock())
        self.array = []
        self.num_blocks = 0
    
    def size(self):
        self.lock.acquire()
        size1 = len(self.array)
        self.lock.release()
        return size1
    
    def get(self, index):
        self.lock.acquire()
        if index < 0 or index >= len(self.array):
            result = None
        else:
            result = self.array[index]
        self.lock.release()
        return result
    
    def set(self, index, value):
        self.lock.acquire()
        if index < 0 or index > len(self.array):
            raise Exception('ERROR: Bad index %s' % index)
        else:
            self.array[index] = value
        self.lock.release()
    
    def append(self, value):
        self.lock.acquire()
        self.array.append(value)
        self.lock.release()

    #def remove(self, index):
    #    print 'ArrayThreadSafe.remove()'
    #    self.lock.acquire()
    #    if index < 0 or index > len(self.array):
    #        print 'ERROR: Bad index %s' % index
    #    else:
    #        print 'ArrayThreadSafe.remove(): removing item %s' % index
    #        for item in self.array:
    #            print '  item: %s' % item
    #        print 'After delete:'
    #        del self.array[index]
    #        for item in self.array:
    #            print '  item: %s' % item
    #        self.lock.notifyAll()
    #    self.lock.release()
    
    def remove_value(self, value):
        #print 'ArrayThreadSafe.remove_value()'
        self.lock.acquire()
            
        index = None
        for i in range(len(self.array)):
            if self.array[i] == value:
                index = i
                break
        
        if index is None:
            raise Exception('ERROR: Value "%s" not found.' % value)
        else:
            del self.array[index]
            self.lock.notifyAll()
        self.lock.release()
    
    def has(self, value):
        result = False
        self.lock.acquire()
        while item in self.array:
            if item == value:
                result = True
                break
        self.lock.release()
        return result
    
    def block_and_append(self, value):
        'Tries to add a value to the list.  If the value exists already, block until it\'s removed.'
        self.lock.acquire()
        
        #print 'ArrayThreadSafe.block_and_append()'
        
        first = True
        while True:
            result = False
            for item in self.array:
                if item == value:
                    result = True
                    break
            
            if not result:
                # Value doesn't exist in array, add it and break
                #print 'ArrayThreadSafe.block_and_append(): adding "%s" to the array' % value
                self.array.append(value)
                break
            else:
                # Value already exist, wait until it doesn't
                if first:
                    #print 'ArrayThreadSafe.block_and_append(): waiting...'
                    first = False
                
                #for item in self.array:
                #    print '  item: %s' % item
                
                self.lock.wait()
                
        self.lock.release()
        return result
    
class CheckUrlOpener(urllib.FancyURLopener):
    def __init__(self, *args, **kwargs):
        #print 'CheckUrlOpener.__init__()'
        urllib.FancyURLopener.__init__(self, *args, **kwargs)
        self.is_bad_url = False
        self.error_str = None
        
    def http_error_default(self, request, file1, code, msg, headers):
        #print 'http_error_default()'
        #print '  request: %r' % request
        #print '  file1: %r' % file1
        #print '  code: %r' % code
        #print '  msg: %r' % msg
        #print '  headers: %r' % headers
        self.is_bad_url = True
        self.error_str = 'HTTP %s: %s' % (code, msg)

def check_url(url, timeout=None):
    '''
    Checks a single URL.
    @param url: the URL to check.
    @return: A tuple (url_status, url_error), where url_status is 'good' or 'bad' or '', and url_error is the error message.
    '''
    opener = CheckUrlOpener()
    url_status = ''
    url_error = ''
    
    if timeout is not None:
        old_socket_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
    
    try:
        opener.open(url)
    
    except socket.timeout, e:
        url_status = Resource.URL_STATUS_BAD
        url_error = 'Timed out'
        
    except socket.error, e:
        url_error = 'Socket Error: %s' % e
        url_status = Resource.URL_STATUS_BAD
        
    except IOError, e:
        error_type = e.args[0]
        if error_type == 'socket error':
            if type(e.args[1]) is socket.timeout:
                url_error = 'Timed out'
            else:
                error_num, error_msg = e.args[1]
                if error_num == 11001:
                    # getaddrinfo failed - bad host name
                    url_error = 'Bad hostname'
                else:
                    url_error = 'Error #%s: %s' % (error_num, error_msg)
        else:
            # Unknown exception
            url_error = str(e)
        url_status = Resource.URL_STATUS_BAD
    
    except UnicodeError:
        url_error = 'URL contains non-ASCII characters.'
        url_status = Resource.URL_STATUS_BAD
        
    else:
        # No exceptions, check for HTTP errors
        opener.close()
        if opener.is_bad_url:
            # Got an HTTP error
            url_status = Resource.URL_STATUS_BAD
            url_error = opener.error_str

    if timeout is not None:
        socket.setdefaulttimeout(old_socket_timeout)

    return (url_status, url_error)

def check_url_thread(resource_queue, resources_to_save_queue, checking_hosts):
    'A single URL checking thread.'
    thread = threading.currentThread()
    #print '  %s: check_url_thread()' % thread.getName()
    while True:
        try:
            resource = resource_queue.get(block=False)
        except Empty:
            break
        
        #print '  %s: checking %s' % (thread.getName(), resource.url)
        opener = CheckUrlOpener()
        bad_url = False
        
        # Check if the host is being checked right now... wait until it's not
        
        urlparts = urlparse.urlparse(resource.url)
        hostname = urlparts.netloc
        
        #print '  %s:   adding %s to checking_hosts' % (thread.getName(), hostname)
        checking_hosts.block_and_append(hostname)
        
        try:
            opener.open(resource.url)
        
        except socket.timeout, e:
            #print 'Got socket.timeout'
            resource.url_error = 'Timed out'
            bad_url = True
            
        except socket.error, e:
            #print 'Got socket.error, %s' % e
            resource.url_error = 'Socket Error: %s' % e
            bad_url = True
            
        except IOError, e:
            #print 'Got IOError'
            #print '  got socket error: %s' % e
            #print '  got socket error r: %r' % e
            #print '  e.args: %s' % str(e.args)
            error_type = e.args[0]
            #print 'error_type: %r' % error_type
            if error_type == 'socket error':
                #print '    Got IOError %s for resource %s' % (e, resource)
                #print 'e.args[1]: %r' % e.args[1]
                #print 'type(e.args[1]): %r' % type(e.args[1])
                
                if type(e.args[1]) is socket.timeout:
                    #print '    Got socket.timeout, %s' % resource.url
                    resource.url_error = 'Timed out'
                else:
                    error_num, error_msg = e.args[1]
                    if error_num == 11001:
                        # getaddrinfo failed - bad host name
                        #print '    bad host name'
                        resource.url_error = 'Bad hostname'
                    else:
                        #print '    Unknown error_num %s' % error_num
                        #print '    error_msg: %s' % error_msg
                        resource.url_error = 'Error #%s: %s' % (error_num, error_msg)
            else:
                # Unknown exception
                #print '    Unknown error_type: %s' % error_type
                resource.url_error = str(e)
            
            bad_url = True
        
        except UnicodeError:
            #print 'Got unicode error'
            resource.url_error = 'URL contains non-ASCII characters.'
            bad_url = True
            
        else:
            # No exceptions, check for HTTP errors
            opener.close()
            if opener.is_bad_url:
                # Got an HTTP error
                #print '    Got bad resource %s' % resource
                #print 'Got HTTP error: %s' % opener.error_str
                bad_url = True
                resource.url_error = opener.error_str
        
        #print '  %s:   Removing %s from checking_hosts' % (thread.getName(), hostname)
        checking_hosts.remove_value(hostname)
        
        if bad_url:
            resource.url_status = Resource.URL_STATUS_BAD
        else:
            resource.url_status = Resource.URL_STATUS_GOOD
            resource.url_error = ''
            
        #print '  %s: resource.url: %s' % (thread.getName(), resource.url)
        #print '  %s: resource.url_status: %s' % (thread.getName(), resource.url_status)
        #print '  %s: resource.url_error: %s' % (thread.getName(), resource.url_error)
        resource.url_date_checked = datetime.datetime.now()
        
        #print '  %s: adding resource to resources_to_save_queue' % (thread.getName())
        resources_to_save_queue.put(resource)
        
        resource_queue.task_done()
    #print '  %s: ~check_url_thread()' % thread.getName()

def save_resources_main(resource_queue):
    'Save any pending resources.'
    #print 'save_resources_main()'
    while True:
        #print 'save_resources_main(): waiting for resource_queue.'
        resource = resource_queue.get()
        if resource is None:
            #print 'save_resources_main(): resource is None, quitting.'
            break
        
        #print 'Saving resource %s' % resource.id
        #print '  resource.url: %s' % resource.url
        #print '  resource.url_status: %s' % resource.url_status
        #print '  resource.url_error: %s' % resource.url_error
        resource.save()
        resource_queue.task_done()
    #print '~save_resources_main()'

def check_resources(resources, num_threads):
    """
    Takes a list of resources and checks all the URLs.
    @param resources A list of resources to check.
    @param num_threads The number of concurrent threads to use for checking URLs.
    Returns a list of all resources with invalid URLs.
    """
    #print 'check_resources()'
    
    # Set the global socket timeout
    old_socket_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(10)
    #print '  old_socket_timeout: %s' % old_socket_timeout
    
    
    log = UrlCheckerLog()
    log.status = 'Started checking resources.'
    log.save()
    
    num_resources = resources.count()
    
    # Add all the resources to a queue
    resource_queue = Queue()
    for resource in resources:
        resource_queue.put(resource)
    
    # Keep track of which resources we need to save
    resources_to_save_queue = Queue()
    
    checking_hosts = ArrayThreadSafe()
    
    # Start all the threads
    threads = []
    for i in range(num_threads):
        thread = threading.Thread(name='Thread %s' % i, target=check_url_thread, args=[resource_queue, resources_to_save_queue, checking_hosts])
        thread.start()
        threads.append(thread)
    
    last_time = time.clock()
    last_num_resources = resource_queue.qsize()
    
    # Start the saving thread
    save_resources_thread = threading.Thread(target=save_resources_main, args=[resources_to_save_queue])
    save_resources_thread.start()
    
    # Loop while URLs are being checked
    while not resource_queue.empty():
        
        # Refresh the log from the DB
        log = UrlCheckerLog.objects.get(id=log.id)
        
        if log.date_ended is not None:
            # Checking was cancelled
            log.status = 'Done checking resources.'
            #print 'Done checking resources.'
            log.save()
            
            # Cancelled, empty the queue so threads will stop
            while resource_queue.qsize():
                try:
                    resource_queue.get_nowait()
                except Empty:
                    pass
        else:
            # Update the log
            if (time.clock() - last_time) > 0:
                speed = (last_num_resources - resource_queue.qsize()) / (time.clock() - last_time)
                log.status = '%s resources remaining (%s resources/sec).' % (resource_queue.qsize(), speed)
                #print '%s resources remaining (%s resources/sec).' % (resource_queue.qsize(), speed)
                log.save()
                last_time = time.clock()
                last_num_resources = resource_queue.qsize()
            time.sleep(5)
    
    # Wait for all threads to die
    #for i in range(num_threads):
    #    print 'Waiting for thread %s to quit.' % i
    #    threads[i].join()

    # Wait for all threads to die
    while len(threads):
        i = 0
        while i < len(threads):
            if not threads[i].isAlive():
                del threads[i]
            else:
                i += 1
        #print 'Waiting for %s threads to die.' % len(threads)
        if len(threads):
            # Either wait for the first thread to end, or 2 seconds (whichever comes first)
            threads[0].join(2)
        
    #print 'checking_hosts.size(): %s' % checking_hosts.size()
    
    # Signal save_resources_thread to stop.
    #print 'Waiting for save_resources_thread to stop.'
    resources_to_save_queue.put(None)
    save_resources_thread.join()
    
    
    if log.date_ended is None:
        # Was not cancelled
        log.status = 'Done checking resources.'
        log.date_ended = datetime.datetime.now()
        log.save()
    
    # Restore the socket timeout
    socket.setdefaulttimeout(old_socket_timeout)
    
    #print '~check_resources()'
