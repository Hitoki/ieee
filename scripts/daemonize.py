'''
Simple daemonizing functions.  Allows easy conversion of a process into a unix daemon.
See main() for examples.

'''
import os
import time
import sys
import atexit
import resource
import errno

MAXFD = 2048

# Copied from python-daemon 1.6:    
def get_maximum_file_descriptors():
    """ Return the maximum number of open file descriptors for this process.

        Return the process hard resource limit of maximum number of
        open file descriptors. If the limit is "infinity", a default
        value of 'MAXFD' is returned.

        """
    limits = resource.getrlimit(resource.RLIMIT_NOFILE)
    result = limits[1]
    if result == resource.RLIM_INFINITY:
        result = MAXFD
    return result

# Copied from python-daemon 1.6:    
def close_all_open_files(exclude=set()):
    """ Close all open file descriptors.

        Closes every file descriptor (if open) of this process. If
        specified, 'exclude' is a set of file descriptors to *not*
        close.

        """
    print 'close_all_open_files()'
    maxfd = get_maximum_file_descriptors()
    for fd in reversed(range(maxfd)):
        #print '  fd: %r' % fd
        if fd not in exclude:
            close_file_descriptor_if_open(fd)
        else:
            print '  exclude %s!' % fd

class DaemonError(Exception):
    """ Base exception class for errors from this module. """

class DaemonOSEnvironmentError(DaemonError, OSError):
    """ Exception raised when daemon OS environment setup receives error. """

def close_file_descriptor_if_open(fd):
    """ Close a file descriptor if already open.

        Close the file descriptor 'fd', suppressing an error in the
        case the file was not open.

        """
    try:
        os.close(fd)
    except OSError, exc:
        if exc.errno == errno.EBADF:
            # File descriptor was not open
            pass
        else:
            error = DaemonOSEnvironmentError(
                u"Failed to close file descriptor %(fd)d"
                u" (%(exc)s)"
                % vars())
            raise error

def daemonize(stdout=None, stderr=None, stdin=None, pidfilename=None, exclude_files=[]):
    '''
    This daemonizes the current process.  The parent will exit immediately, only the grand-child will still be alive.
    Redirects stdin/stdout/stderr, changes root dir.
    Optionally creates pidfile & takes care of deleting it at program exit.  NOTE: Not a lockfile.
    '''
    try: 
        pid = os.fork() 
        if pid > 0:
            # Exit first parent.
            sys.exit(0) 
    except OSError, e: 
        sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

    # Decouple from parent environment.
    os.chdir("/") 
    os.setsid() 
    os.umask(0) 

    # Do second fork
    try: 
        pid = os.fork() 
        if pid > 0:
            # Exit from second parent
            sys.exit(0)
    except OSError, e: 
        sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1) 

    # redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    
    if stdout is None:
        stdout = open(os.devnull, 'w', 0)
    if stderr is None:
        stderr = open(os.devnull, 'w', 0)
    if stdin is None:
        stdin = open(os.devnull, 'r')
    
    print '  sys.stdout.fileno(): %s' % sys.stdout.fileno()
    print '  sys.stderr.fileno(): %s' % sys.stderr.fileno()
    print '  sys.stdin.fileno(): %s' % sys.stdin.fileno()
    
    print '  stdout.fileno(): %s' % stdout.fileno()
    print '  stderr.fileno(): %s' % stderr.fileno()
    print '  stdin.fileno(): %s' % stdin.fileno()
    
    # Write the pidfile.
    if pidfilename is not None:
        pidfilename = os.path.abspath(pidfilename)
        
        pidfile = open(pidfilename, 'w', 0)
        pidfile.write(str(os.getpid()))
        pidfile.close()
        
        atexit.register(undaemonize, pidfilename)
    
    print 'closing files...'
    
    # Close any open files.
    exclude_files = set(exclude_files)
    exclude_files.add(stdout.fileno())
    exclude_files.add(stderr.fileno())
    exclude_files.add(stdin.fileno())
    
    for f in exclude_files:
        print '  excluding %r' % f
    close_all_open_files(exclude_files)
    
    # Redirect system streams.
    os.dup2(stdout.fileno(), sys.stdout.fileno())
    os.dup2(stderr.fileno(), sys.stderr.fileno())
    os.dup2(stdin.fileno(), sys.stdin.fileno())
    
    
    print 'done closing files.'
    
def undaemonize(pidfilename):
    'Remove the pidfile if it exists.'
    if os.path.exists(pidfilename):
        os.remove(pidfilename)
    
def main():
    pidfilename = os.path.abspath(os.path.join(os.path.dirname(__file__), 'pidfile'))
    logfile = open('log', 'w', 0)
    
    # When this function returns, we will be within the new grandchild process.  The parent process will already have exited.
    daemonize(stdout=logfile, stderr=logfile, pidfilename=pidfilename)
    
    # Now we're in daemon mode.
    
    print 'Sleeping for 5s...'
    time.sleep(5)
    
    print 'Quitting.'
    
if __name__ == '__main__':
    main()
