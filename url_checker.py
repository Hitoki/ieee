import socket
import time
import threading
import urllib
from Queue import Empty, Queue
from ieeetags.models import *
import datetime

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
        
def check_url_thread(resource_queue, bad_resource_queue):
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
        
        try:
            opener.open(resource.url)
        
        except socket.timeout, e:
            #print 'Got socket.timeout'
            resource.url_error = 'Timed out'
            bad_url = True
            
        except socket.error, e:
            #print 'Got socket.error'
            #print 'e.args: %s' % str(e.args)
            resource.url_error = 'Socket Error'
            bad_url = True
            raise
            
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
                    #print '    Got socket.timeout'
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
            resource.url_error = 'URL contains non-ASCII characters.'
            bad_url = True
            
        else:
            # No exceptions, check for HTTP errors
            opener.close()
            if opener.is_bad_url:
                # Got an HTTP error
                #print '    Got bad resource %s' % resource
                #print '    Got bad resource, error_str: %s' % opener.error_str
                bad_url = True
                resource.url_error = opener.error_str
            
        
        if bad_url:
            resource.url_status = Resource.URL_STATUS_BAD
        else:
            resource.url_status = Resource.URL_STATUS_GOOD
        resource.url_date_checked = datetime.datetime.now()
        
        bad_resource_queue.put(resource)
        
        resource_queue.task_done()
    #print '  %s: ~check_url_thread()' % thread.getName()

def check_resources(resources, num_threads):
    """
    Takes a list of resources and checks all the URLs.
    @param resources A list of resources to check.
    @param num_threads The number of concurrent threads to use for checking URLs.
    Returns a list of all resources with invalid URLs.
    """
    print 'check_resources()'
    
    # Set the global socket timeout
    old_socket_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(5)
    #print '  old_socket_timeout: %s' % old_socket_timeout
    
    
    log = UrlCheckerLog()
    log.status = 'Started checking resources.'
    log.save()
    
    num_resources = resources.count()
    
    resource_queue = Queue()
    for resource in resources:
        resource_queue.put(resource)
    
    bad_resource_queue = Queue()
    
    #print 'starting threads'
    threads = []
    for i in range(num_threads):
        thread = threading.Thread(name='Thread %s' % i, target=check_url_thread, args=[resource_queue, bad_resource_queue])
        thread.start()
        threads.append(thread)
    #print 'done starting threads'
    
    last_time = time.clock()
    last_num_resources = resource_queue.qsize()
    
    while resource_queue.qsize() > 0:
        
        # Save any pending bad resources
        while True:
            try:
                resource = bad_resource_queue.get_nowait()
            except Empty:
                break
            else:
                resource.save()
                bad_resource_queue.task_done()
        
        # Refresh the log from the DB
        log = UrlCheckerLog.objects.get(id=log.id)
        
        if log.date_ended is not None:
            # Checking was cancelled
            log.status = 'Done checking resources.'
            print 'Done checking resources.'
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
                print '%s resources remaining (%s resources/sec).' % (resource_queue.qsize(), speed)
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
        print 'Waiting for %s threads to die.' % len(threads)
        time.sleep(2)
    
    
    if log.date_ended is None:
        # Was not cancelled
        log.status = 'Done checking resources.'
        log.date_ended = datetime.datetime.now()
        log.save()
    
    # Restore the socket timeout
    socket.setdefaulttimeout(old_socket_timeout)
    
    print '~check_resources()'
