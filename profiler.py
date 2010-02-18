from logging import debug as log
import time
from util import odict

class Profiler:
    '''
    Used to manually profile functions and see where time is being spent.
    
    Usage:
        p = Profiler('page number 1')
        # ...
        p.tick('Before action X')
        # ... 
        p.tick('Before action Y')
        # ... 
        for i in range(10):
            p.start_loop()
            # ... 
            p.tick('Before action Z')
            # ... 
            p.end_loop()
        
    Prints all output to the log.
    '''
    def __init__(self, name=''):
        self.name = name
        self.is_loop = False
        log('profile %s: -- start ------------' % name)
        self.start_time = time.time()
        self.loop_start_time = None
        self.last_loop_time = None
    
    def __del__(self):
        log('profile %s: %0.2fs -- end ----------' % (self.name, time.time() - self.start_time))
    
    def tick(self, name):
        if self.is_loop:
            if name not in self.ticks:
                self.ticks[name] = 0
            now = time.time()
            seconds = now - self.last_loop_time
            self.last_loop_time = now
            self.ticks[name] += seconds
        else:
            log('profile %s: %0.2fs - %s' % (self.name, time.time() - self.start_time, name))
    
    def start_loop(self):
        self.is_loop = True
        self.loop_start_time = time.time()
        self.last_loop_time = self.loop_start_time
        self.ticks = odict()
        log('profile %s: %0.2fs - START LOOP' % (self.name, time.time() - self.start_time))
    
    def end_loop(self):
        self.is_loop = False
        self.loop_start_time = None
        
        for name, value in self.ticks.items():
            log('profile %s: %0.2fs - total for loop tick "%s"' % (self.name, value, name))
        
        log('profile %s: %0.2fs - END LOOP' % (self.name, time.time() - self.start_time))
