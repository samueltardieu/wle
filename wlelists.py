#
# $Id$
#
# Lists handling
#

import email.Message, os, re, time
import wleconfig, wleconfirm, wledb, wlemail, wlelog
from wlestats import count_authorized

#
# Check if one of the strings (email address) is in the confirmed list
# (no regexp, no prefix)
#

def is_in_confirmed_list (str, c = None):
    for i in str:
        if wledb.check_presence ("confirmed", "email", i.lower(), c):
            return True
    return False

#
# Check if at least one entry in a list matches a regular expression
#

def matching (regexp, l):
    if l is None: return
    r = re.compile ('(?i)' + regexp)
    for i in l:
        if r.search (i): return True
    return False
    
#
# Check if a message matches a condition described in a list
#

_from_re = re.compile ('(?i)from\s+(.*\S)\s*$')
_to_re = re.compile ('(?i)to\s+(.*\S)\s*$')
_other_re = re.compile ('(?i)(\S+):\s+(.*\S)\s*$')
_comment = re.compile ('(?i)(.*)#')
_empty = re.compile ('(?i)\s*$')

def is_in_list (m, list):
    try:
        l = open (wleconfig.config.get ('DEFAULT', list), 'r')
    except:
        return False
    for i in l.readlines ():
        if i[-1:] == '\n': i = i[:-1]
        x = _comment.match (i)
        if x: i = x.group (1)
        if _empty.match (i): continue
        x = _from_re.match (i)
        if x:
            if matching (x.group (1), m.msenders): return i
        else:
            x = _to_re.match (i)
            if x:
                if matching (x.group (1), m.mrecipients): return i
            else:
                x = _other_re.match (i)
                if x:
                    if matching (x.group (2), m.get_all (x.group(1))):
                        return i
                else:
                    if matching (i, m.msenders): return i
    return False

#
# Add a list of addresses to the confirmed list if they are not there
# already there or in the whitelist
#

_well_formed_re = re.compile ('\S+@\S+\.\S+$')

def add_confirmed (l):
    db = wledb.connect_db ()
    c = db.cursor ()
    for i in l:
        if not _well_formed_re.match (i): continue
        m = email.Message.Message ()
        m['From'] = i
        wlemail.parse_message (m)
        if is_in_list (m, 'whitelist'): continue
        if wleconfirm.is_mine ([i]): continue
        if not is_in_confirmed_list ([i], c):
            wlelog.log (2, 'Adding %s as authorized address' % i)
            c.execute ("insert into confirmed values ('%s', %f)" %
                       (i.lower(), time.time ()))
            count_authorized ()
            wleconfirm.also_unblock (i)            
    db.commit ()

#
# Snoop addresses in messages
#

def snoop_addresses (m):
    max_confirm = wleconfig.config.getboolean ('DEFAULT', 'max_confirm')
    if max_confirm: add_confirmed (m.msenders)
    else: add_confirmed (m.msenders[:1])

