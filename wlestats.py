#
# $Id$
#

import os.path
import wleconfig

def count (name):
    if not wleconfig.config.getboolean ('DEFAULT', 'stats_' + name): return
    statsdir = wleconfig.config.get ('DEFAULT', 'statsdir')
    open (os.path.join (statsdir, name), 'a+b').write('.')

# Various stats

def count_received (): count ('received')
def count_confirmed (): count ('confirmed')
def count_rejected (): count ('rejected')
def count_junk (): count ('junk')
def count_bulk (): count ('bulk')
def count_authorized (): count ('authorized')
def count_delivered (): count ('delivered')
def count_queued (): count ('queued')
