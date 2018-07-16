
import time

class Timer(object):
    '''
    Usage:
    with Timer() as t:
        [run method to be timed]
    print("some words: %s s" % t.secs)
    
    or the following will output as milliseconds "elapsed time: [time] ms":
    with Timer(verbose = True) as t:
        [run method to be timed]
    '''
    
    def __init__(self, verbose=False):
        self.verbose = verbose

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000  # millisecs
        if self.verbose:
            print("elapsed time: %f ms" % self.msecs)



    
