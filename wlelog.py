#
# $Id$
#
# Log file handling
#

import time, wleconfig

_first = 1

def logfile ():
    return wleconfig.config.get ('DEFAULT', 'logfile')

def loglevel ():
    return wleconfig.config.getint ('DEFAULT', 'loglevel')

def log (n, str):
    global _first
    if n <= loglevel():
        fd = open (logfile(), 'a')
        if _first:
            fd.write ('%s\n' % ('-' * 70))
            _first = 0
        fd.write ('%s %s\n' % (time.ctime (time.time()), str))

