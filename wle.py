#! /usr/local/bin/python
#
# $Id$
#

INSTALLDIR = '/home/sam/Dev/WLE'

import sys
sys.path.append (INSTALLDIR)

import email.Parser
import wleconfirm, wlemail, wlelists, wlelog, wlelock, wleconfig, wlevacation
from wlestats import count_received, count_confirmed, count_rejected, \
     count_bulk, count_junk, count_queued, count_delivered

def handle_confirmation (m, key):
    wlelog.log (3, 'Confirmation found with key %s' % key)
    unqueued = wleconfirm.deliver (key)
    wlelists.snoop_addresses (unqueued)
    wleconfirm.check_discuss (unqueued)
    if wleconfig.config.getboolean ('DEFAULT', 'allow_confirmer'):
        wlelists.snoop_addresses (m)
    wleconfirm.deliver_mail (m, 'confirmedbox')

def handle_ok (m):
    wlemail.add_magic (m)
    wlevacation.handle_incoming (m)
    wleconfirm.deliver_mail (m, 'mailbox')
    count_delivered ()
    wleconfirm.check_discuss (m)
    if wlemail.from_mailinglist (m):
        if wleconfig.config.getboolean ('DEFAULT', 'list_add_other'):
            wlelists.snoop_addresses (m)
    else:
        if wlemail.sent_by_myself (m):
            if wleconfig.config.getboolean ('DEFAULT', 'confirm_recipients'):
                wlelists.add_confirmed (m.mrecipients)
        elif wleconfig.config.getboolean ('DEFAULT', 'people_add_other'):
            wlelists.snoop_addresses (m)

def log_summary (m):
    for i in ['From', 'Subject', 'To', 'Cc', 'Bcc', 'Message-Id']:
        if m.has_key (i):
            wlelog.log (5, '%s: %s' % (i, m[i]))

def logic (m):
    count_received ()
    wlemail.parse_message (m)
    log_summary (m)
    if wleconfirm.is_old_confirm (m):
        wlemail.add_action (m, 'Related to an old confirmation request')
        wleconfirm.deliver_mail (m, 'confirmedbox')
        return
    if wlemail.from_mailerdaemon (m):
        key = wleconfirm.is_confirm (m)
        if key:
            wlemail.add_action (m, 'Bounce of confirmation request')
            count_junk ()
            wleconfirm.deliver_mail (m, 'junkbox')
            if wleconfig.config.getboolean ('DEFAULT', 'auto_delete_bounce'):
                count_rejected ()
                try:
                    wleconfirm.move_message_from_queue (key,
                                                        'junkbox',
                                                        'Confirmation bounced')
                except:
                    pass
            return
	if wlemail.sent_to_me (m):
	    wlemail.add_action (m, 'Mailer daemon get through')
	    wlemail.add_magic (m)
	    wleconfirm.deliver_mail (m, 'mailbox')
	    return
	else:
	    wlemail.add_action (m, 'Suspect mailer daemon message')
	    wleconfirm.deliver_mail (m, 'junkbox')
	    return
    key = wleconfirm.is_confirm (m)
    if key:
        if not wlemail.is_junk (m):
            count_confirmed ()
            wlelog.log (3, 'Found key in mail')
            handle_confirmation (m, key)
            return
        wlelog.log (3, 'Will not accept confirmation from junk message')
    x = wlelists.is_in_list (m, 'ignorelist')
    if x:
        wlemail.add_action (m, 'Ignore list (%s), junk box' % x)
        wleconfirm.deliver_mail (m, 'junkbox')
        count_junk ()
        return
    x = wlemail.contains_command (m)
    if x:
        x (m)
        return
    if wlemail.contains_magic (m):
        wlemail.add_action (m, 'Message contains magic number')
        handle_ok (m)
        if wleconfig.config.getboolean ('DEFAULT', 'magic_add_sender'):
            wlelists.snoop_addresses (m)
        return
    x = wlelists.is_in_list (m, 'whitelist')
    if x:
        wlemail.add_action (m, 'White list (%s)' % x)
        handle_ok (m)
        if wleconfig.config.getboolean ('DEFAULT', 'confirm_whitelist'):
            wlelists.add_confirmed (m.msenders)
        return
    if wlelists.is_in_confirmed_list (m.msenders):
        wlemail.add_action (m, 'Sender found in authorized list')
        handle_ok (m)
        return
    if wlemail.from_mailinglist (m):
        wlemail.add_action (m, 'Bulk mail')
        wleconfirm.deliver_mail (m, 'bulkbox')
        count_bulk ()
        return
    if wlemail.is_junk (m):
        wlemail.add_action (m, 'Junk mail')
        wleconfirm.deliver_mail (m, 'junkbox')
        count_junk ()
        return
    # A new confirmation request is a good time to cleanup databases
    wleconfirm.cleanup_dbs ()
    wleconfirm.queue (m)
    count_queued ()
    return

try:
    wleconfig.read_config ()
    wlelog.log (9, 'Starting')
    wlelock.lock ()
    wlelog.log (9, 'Lock taken')
    try:
        logic (email.Parser.Parser().parse(sys.stdin))
    except:
        wlelog.log (1, 'Exception raised')
        t, v, tb = sys.exc_info ()
        import traceback
        lines = traceback.format_exception (t, v, tb)
        for i in lines:
            sys.stderr.write (i)
            wlelog.log (2, i[:-1])
        sys.exit (1)
finally:
    wlelog.log (9, 'Releasing lock')
    wlelock.unlock ()
wlelog.log (9, 'Exiting')
