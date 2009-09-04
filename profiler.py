from logging import debug as log
import time
from util import odict

class Profiler:
    def __init__(self, name=''):
        self.name = name
        self.is_loop = False
        log('profile %s: -- start ------------' % name)
        self.start_time = time.time()
        self.loop_start_time = None
        self.last_loop_time = None
    
    def __del__(self):
        seconds = round(time.time() - self.start_time, 1)
        log('profile %s: %ss -- end ----------' % (self.name, seconds))
    
    def tick(self, name):
        if self.is_loop:
            if name not in self.ticks:
                self.ticks[name] = 0
            now = time.time()
            seconds = now - self.last_loop_time
            self.last_loop_time = now
            self.ticks[name] += seconds
        else:
            seconds = round(time.time() - self.start_time, 1)
            log('profile %s: %ss - %s' % (self.name, seconds, name))
    
    def start_loop(self):
        self.is_loop = True
        self.loop_start_time = time.time()
        self.last_loop_time = self.loop_start_time
        self.ticks = odict()
        seconds = round(time.time() - self.start_time, 1)
        log('profile %s: %ss - START LOOP' % (self.name, seconds))
    
    def end_loop(self):
        self.is_loop = False
        self.loop_start_time = None
        
        for name, value in self.ticks.items():
            seconds = round(value, 1)
            log('profile %s: %ss - total for loop tick "%s"' % (self.name, seconds, name))
        
        seconds = round(time.time() - self.start_time, 1)
        log('profile %s: %ss - END LOOP' % (self.name, seconds))
