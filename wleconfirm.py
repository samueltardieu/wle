#
# $Id$
#
# Confirmation handling
#

import wlelog, wlequeue, wleconfig, wlemail, wlevacation
import email.Header, email.Parser, md5, re, os.path, shelve, string, time
from email.MIMEMessage import MIMEMessage
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

#
# My own addresses
#

def myself ():
    return re.split ('\s*,\s*',
                     wleconfig.config.get ('DEFAULT', 'myaddresses'))

#
# Check if a given address list contains one of mine
#

def is_mine (l):
    my_addresses = myself()
    for i in l:
        if type(i) == type(()): i = i[1]
        for j in my_addresses:
            if re.match ('(?i)' + j + '$', i): return i
    return None

#
# Find the originator address to use
#

def confirmation_sender (m):
    addr = is_mine (wlemail.recipients (m))
    if addr: return addr
    else: return myself()[0]

def can_send_confirmation (recipient):
    db = confirmations_db ()
    if not db.has_key (recipient): return True
    mdh = wleconfig.config.getfloat ('DEFAULT', 'minimum_delay_hours')
    return (time.time() - db[recipient]) / 3600 >= mdh

#
# Cleanup dbs
#

def cleanup_dbs ():
    min = time.time () - \
          86400 * wleconfig.config.getfloat ('DEFAULT', 'cleanup_days')
    for db in [old_requests_db(), confirmations_db()]:
        for k in db.keys():
            if db[k] < min:
                wlelog.log (7, "Cleaning up record %s" % k)
                del db[k]

#
# Make excuse message
#

def makeup_excuse (key):
    languages = re.split ('\s*,\s*',
                          wleconfig.config.get ('DEFAULT', 'languages'))
    templatesdir = wleconfig.config.get ('DEFAULT', 'templatesdir')
    t = ''
    for i in languages:
        t = t + (open ("%s/%s.txt" % (templatesdir, i)).read()) % {'key': key}
        t = t + '\n' + ('-' * 72) + '\n'
    return t

#
# Prepare confirmation message for message m with a confirmation key. Also,
# explain what has been done
#

def confirmation (m, key):
    recipient = wlemail.senders(m)[0]
    recipient_email = recipient[1]
    if not can_send_confirmation (recipient_email):
        wlelog.log (3, "Not sending duplicate confirmation to %s" % \
                    email.Utils.formataddr (recipient))
        return None
    wlelog.log (3, "Sending confirmation request to %s" % \
                email.Utils.formataddr (recipient))
    r = MIMEMultipart ()
    subject = m.get ('subject')
    if not subject: subject = '...'
    rsubject = '[confirm #%s] %s' % (key, wlemail.make_answer (subject))
    r['X-WLE-confirmation'] = 'yes'
    r['Precedence'] = 'bulk'
    rfrom = email.Utils.formataddr \
            ((wleconfig.config.get ('DEFAULT', 'myname'),
              confirmation_sender (m)))
    rto = email.Utils.formataddr (recipient)
    wlemail.complete_message (r, rfrom, rto, rsubject)
    try: r['In-Reply-To'] = m.get ('message-id')
    except: pass
    excuse = MIMEText (makeup_excuse (key), 'plain',
                       wleconfig.config.get ('DEFAULT', 'charset'))
    excuse['Content-Disposition'] = 'inline'
    r.attach (excuse)
    origin = MIMEMessage (m)
    origin['Content-Disposition'] = 'attachment'
    r.attach (origin)
    confirmations_db()[recipient_email] = time.time()
    return r

#
# Compute message secret
#

def secret (m):
    s = md5.new ()
    s.update (wleconfig.config.get ('DEFAULT', 'secret'))
    s.update (m.as_string ())
    return s.hexdigest () [:16]

#
# Store a message in the queue and send the confirmation
#

def queue_path (key):
    return "%s/%s" % (wleconfig.config.get ('DEFAULT', 'queuedir'), key)

def queue (m):
    key = secret (m)
    fd = open (queue_path (key), 'w')
    wlemail.add_action (m, "Queued (%s)" % time.ctime (time.time()))
    fd.write (m.as_string ())
    fd.close ()
    confirm = confirmation (m, key)
    if confirm: wlemail.send_message (confirm)

#
# Test whether a message is a confirmation message
#

_confirm_re = re.compile ('confirm #([\da-z]{16})')

def is_key (x):
    if os.path.exists (queue_path (x)): return x
    return False

def decoded_header (s):
    return string.join (map (lambda (x,y): x, email.Header.decode_header (s)))

def is_confirm (m):
    x = _confirm_re.search (m.as_string())
    if x: return is_key (x.group (1))
    if m.has_key ('subject'):
        subject = decoded_header (m['subject'])
        x = _confirm_re.search (subject)
        if x: return is_key (x.group (1))
    return False

def old_requests_db ():
    return shelve.open (wleconfig.config.get ('DEFAULT', 'old_requests'))

def confirmations_db ():
    return shelve.open (wleconfig.config.get ('DEFAULT', 'confirmations'))

def is_old_confirm (m):
    x = _confirm_re.search (m.as_string())
    if x: return old_requests_db().has_key(x.group(1))
    return False

#
# Deliver a message in a mailbox or to a program
#

def deliver_mail (m, mailbox):
    mn = wleconfig.config.get ('DEFAULT', mailbox)
    if mn[0] == '|':
        wlelog.log (4, "Delivering to program %s" % string.strip (mn[1:]))
        fd = os.popen (mn[1:], 'w')
    else:
        wlelog.log (4, "Delivering to mailbox %s" % string.strip (mn))
        fd = open (mn, 'a')
    fd.write (m.as_string (True))

#
# Open a message by its key number
#

def open_by_key (key):
    fn = queue_path (key)
    fd = open (fn, 'r')
    m = email.Parser.Parser().parse (fd)
    wlemail.parse_message (m)
    fd.close ()
    return m

#
# Remove message in queue
#

def remove_message (key):
    wlelog.log (5, "Removing queue file %s" % key)
    os.unlink (queue_path (key))
    old_requests_db()[key] = time.time ()

#
# Move message in mailbox and remove from queue. Add an action field and
# a magic if needed. Also return the message itself.
#

def move_message_from_queue (key, mailbox, action, magic = False):
    m = open_by_key (key)
    wlemail.add_action (m, action)
    if magic:
        wlemail.add_magic (m)
        wlevacation.handle_incoming (m)
    deliver_mail (m, mailbox)
    remove_message (key)
    return m
    
#
# Deliver a message and unqueue it. Also returns the message
#

def deliver (key):
    wlelog.log (3, 'Unblocking mail with key %s' % key)
    return move_message_from_queue (key, 'mailbox',
                                    'Confirmed (%s)' % \
                                    time.ctime (time.time()),
                                    True)

#
# Unblock messages whose sender has been confirmed by any other way
#

def also_unblock (s):
    for k in wlequeue.waitinglist():
        try: m = open_by_key (k)
        except: continue
        if s in m.msenders: deliver (k)
