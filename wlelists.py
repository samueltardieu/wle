#
# $Id$
#
# Lists handling
#

import email.Message, re, wleconfig, wleconfirm, wlemail, wlelog

#
# Check if a string (email address) is in a simple list (no regexp, no prefix)
#

def is_in_simple_list (str, list):
    try:
        l = open (wleconfig.config.get ('DEFAULT', list), 'r')
    except:
        return False
    lines = map (lambda x: x[:-1], l.readlines())
    for i in str:
        if i.lower() in lines: return True
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
    for i in l:
        if not _well_formed_re.match (i): continue
        m = email.Message.Message ()
        m['From'] = i
        wlemail.parse_message (m)
        if is_in_list (m, 'whitelist'): continue
        if wleconfirm.is_mine ([i]): continue
        if not is_in_simple_list ([i], 'confirmedlist'):
            wlelog.log (2, 'Adding %s as authorized address' % i)
            fd = open (wleconfig.config.get ('DEFAULT', 'confirmedlist'), 'a')
            fd.write (i.lower() + '\n')
            fd.close ()
            wleconfirm.also_unblock (i)

#
# Snoop addresses in messages
#

def snoop_addresses (m):
    max_confirm = wleconfig.config.getboolean ('DEFAULT', 'max_confirm')
    if max_confirm: add_confirmed (m.msenders)
    else: add_confirmed (m.msenders[:1])

