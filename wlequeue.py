#
# $Id$
#
# Queue processing
#

import wleconfig, wleconfirm, wlemail, wlelog, wlelists
import dircache, email.Utils, os, re, stat, string, time
from email.MIMEText import MIMEText

#
# List of waiting mails, ordered by reverse modification time
#

def waitinglist ():
    queuedir = wleconfig.config.get ('DEFAULT', 'queuedir')
    def mtime (f): return os.stat(os.path.join(queuedir, f))[stat.ST_MTIME]
    def compare(f1, f2): return cmp (mtime(f2), mtime(f1))
    l = dircache.listdir (queuedir)
    l.sort (compare)
    return l

#
# Return the description of one email by key, suitable for later processing
#

def describe (key):
    received = os.stat (wleconfirm.queue_path (key)) [stat.ST_MTIME]
    days = int (time.time() - received) / 86400
    if wleconfig.config.getint ('DEFAULT', 'remove_days') <= days:
        action = 'R'
    else:
        action = 'N'
    m = wleconfirm.open_by_key (key)
    t =     ' [%s] id #%s      %s (%d days)\n' % (action, key, m['date'], days)
    if m.has_key ('from'):
        t = t + '     From: %s\n' % (m['from'])
    if m.has_key ('subject'):
        t = t + '     Subject: %s\n' % (m['subject'])
    if m.has_key ('to'):
        t = t + '     To: %s\n' % (m['to'])
    if m.has_key ('cc'):    
        t = t + '     Cc: %s\n' % (m['cc'])
    if m.has_key ('bcc'):    
        t = t + '     Bcc: %s\n' % (m['bcc'])
    return t

#
# Return a list of waiting emails, suitable for later processing
#

def describe_list (skipempty):
    w = waitinglist()
    if w or not skipempty:
        t = '[N] Do nothing   [W] Whitelist   [D] Deliver   [R] Reject\n'
        for i in w: t = "%s\n%s" % (t, describe(i))
        return t
    return None

#
# Complete and send automatic message
#

def complete_and_send (m, subject, content):
    sender = wleconfirm.confirmation_sender (m)
    wlelog.log (3, 'Sending %s to %s' % (subject, sender))
    rfrom = "WLE email program <%s>" % sender
    rto = email.Utils.formataddr \
          ((wleconfig.config.get ('DEFAULT', 'myname'), sender))
    r = MIMEText (content, 'plain',
                  wleconfig.config.get ('DEFAULT', 'charset'))
    wlemail.complete_message (r, rfrom, rto, subject)
    wlemail.add_magic (r)
    wleconfirm.deliver_mail (r, 'mailbox')

#
# Send a message with the list of queued mails to the sender
#

def handle_command_process_queue (m, skipempty = False):
    r = describe_list (skipempty)
    if r:
        complete_and_send (m, "WLE queue status", r)

#
# Same command but only if the list is not empty
#

def handle_command_process_nequeue (m):
    handle_command_process_queue (m, True)

#
# Help message
#

def handle_command_help (m):
    help = "Commands:\n  WLE queue: return list of waiting messages\n" \
           "  WLE queue status: handle waiting messages\n"
    complete_and_send (m, "WLE help", help)

#
# Handle queue status change
#

_command_re = re.compile ('(?i)\[(\S)\] id #([\da-z]{16})')

def handle_command_queue_status (m):
    wlelog.log (3, 'Working on queue')
    lines = string.split (m.as_string(), '\n')
    for i in lines:
        x = _command_re.search (i)
        if x: handle_action (x.group(1).upper(), x.group(2))
        
#
# Handle individual action
#

def handle_action (action, key):
    if not wleconfirm.is_key (key):
        wlelog.log (4, "%s is not a valid key, ignoring" % key)
        return
    if action == 'W':
        unqueued = wleconfirm.deliver (key)
        wlelists.snoop_addresses (unqueued)
    elif action == 'D':
        wleconfirm.deliver (key)
    elif action == 'R':
        wleconfirm.remove_message (key)
