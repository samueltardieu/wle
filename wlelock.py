#
# $Id$
#
# Lock file support
#

import fcntl, wleconfig

def lock ():
    global _fd
    _fd = open (wleconfig.config.get ('DEFAULT', 'lockfile'), 'w')
    fcntl.flock (_fd, fcntl.LOCK_EX)

def unlock ():
    fcntl.flock (_fd, fcntl.LOCK_UN)
    _fd.close ()


