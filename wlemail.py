#
# $Id$
#
# Bunch of helper routines used to manipulate email content (using class
# Message of the email module)
#

import email.Utils, os, re, wleconfig, wlelog, wleconfirm, time, wlequeue

#
# Return a list of selected fields (which are supposed to be addresses) if
# they are present. Return pairs of (name, address).
#

def fields (m, f):
    r = []
    for i in f: r = r + m.get_all (i, [])
    return email.Utils.getaddresses (r)

#
# Return a list of all message senders. The first address in list will be
# the one the confirmation is sent to.
#

def senders (m):
    r = fields (m, ['errors-to', 'resent-from', 'from', 'reply-to', 'sender',
                    'return-path'])
    if m.get_unixfrom():
        r.append (('', (m.get_unixfrom().split()[1])))
    return r

#
# Return a list of all message recipients
#

def recipients (m):
    return fields (m, ['to', 'cc', 'bcc', 'resent-to', 'resent-cc'])

#
# Determine if mail came through a mailing-list
#

_list_re = re.compile ('(?i)(bulk)|(list)$')

def from_mailinglist (m):
    if m.has_key ('precedence') and _list_re.match (m['precedence']):
        return True
    return m.has_key ('list-unsubscribe')

#
# Determine if mail declares itself junk
#

def is_junk (m):
    return m.has_key ('precedence') and m['precedence'].lower() == 'junk'

#
# Determine if mail comes from mailer-daemon
#

_mailer_daemon_re = re.compile ('(?i)mailer[ -]daemon')
_postmaster_re = re.compile ('(?i)postmaster@')

def from_mailerdaemon (m):
    if m.has_key ('from') and _mailer_daemon_re.match (m['from']):
        return True
    if m.has_key ('return-path') and _postmaster_re.match (m['return-path']):
        return True
    return m['return-path'] == '<>'

#
# Determine if mail contains the magic string
#

def contains_magic (m):
    return m.as_string().find (wleconfig.config.get ('DEFAULT', 'magic')) != -1

#
# Check if mail contains a command (and is sent by myself), and return the
# command if this is the case.
#

_process_queue_re = re.compile ('(?i)wle queue$')
_process_nequeue_re = re.compile ('(?i)wle nequeue$')
_queue_status_re = re.compile('(?i).*wle queue status$')
_help_re = re.compile('(?i)wle help$')

def contains_command (m):
    if m.has_key ('x-wle-magic'): return False
    if not m.has_key ('subject'): return False
    if not sent_by_myself (m): return False
    if _process_queue_re.match (m['subject']):
        return wlequeue.handle_command_process_queue
    if _process_nequeue_re.match (m['subject']):
        return wlequeue.handle_command_process_nequeue
    if _queue_status_re.match (m['subject']):
        return wlequeue.handle_command_queue_status
    if _help_re.match (m['subject']):
        return wlequeue.handle_command_help

#
# Check whether I am the sender of the mail, if this is the case, return
# the address I used
#

def sent_by_myself (m):
    return wleconfirm.is_mine (m.msenders)

#
# Check whether I am in the recipients of the mail
#

def sent_to_me (m):
    return wleconfirm.is_mine (m.mrecipients)

#
# Parse message and initialize common global variables
#

def parse_message (m):
    l = lambda x: x[1]
    m.msenders = map (l, senders (m))
    m.mrecipients = map (l, recipients (m))

#
# Add action to a message
#

def add_action (m, action):
    wlelog.log (4, 'Adding action: %s' % action)
    m['X-WLE-Action'] = action

#
# Add magic to a message
#

def add_magic (m):
    magic = wleconfig.config.get ('DEFAULT', 'magic')
    if m['X-WLE-Magic'] != magic: m['X-WLE-Magic'] = magic

#
# Send a mail
#

def send_message (m):
    fd = os.popen (wleconfig.config.get ('DEFAULT', 'sendmail') + " -t", 'w')
    fd.write (m.as_string (True))

#
# Complete message
#

def complete_message (m, sender, recipient, subject):
    m['From'] = sender
    m['To'] = recipient
    m['Subject'] = subject
    m['Date'] = email.Utils.formatdate (time.time (), True)
    m['Message-ID'] = email.Utils.make_msgid ('wle')

#
# Return a canonical subject
#

_response_re = re.compile ('(?i)ref?: (.*)')

def canonical_subject (s):
    x = _response_re.match (s)
    if x: return x.group (1)
    return s

#
# Make the answer for a given subject
#

def make_answer (s):
    x = _response_re.match (s)
    if x: return s
    return "Re: " + s
