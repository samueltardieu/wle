#
# $Id$
#
# Send vacation messages
#

from email.MIMEText import MIMEText
import email.Utils, shelve, time
import wleconfig, wleconfirm, wlelog, wlemail

#
# Open vacation database
#
def vacation_db ():
    return shelve.open (wleconfig.config.get ('DEFAULT', 'vacation_db'))

#
# Check whether we can send a vacation message, update the database and
# return the message to send or None
#

def vacation_message (m):
    db = vacation_db ()
    recipient = wlemail.senders(m)[0]
    recipient_email = recipient[1]
    target = email.Utils.formataddr (recipient)
    if db.has_key (recipient_email) and \
       time.time () - db[recipient_email] < \
       86400 * wleconfig.config.getint ('DEFAULT', 'vacation_days'):
        wlelog.log (8, "Not sending duplicate vacation message to %s" % target)
        return None
    db[recipient_email] = time.time ()
    my_name = wleconfig.config.get ('DEFAULT', 'myname')
    my_addr = wleconfirm.confirmation_sender (m)
    subject = m['subject'] or "..."
    subject = wleconfirm.decoded_header (subject)
    trimmed_subject = wlemail.canonical_subject (subject)
    t = open (wleconfig.config.get('DEFAULT', 'vacation_msg'), 'r').read() % \
        {'target_name' :    recipient[0],
         'target_email':    recipient_email,
         'target':          target,
         'subject':         subject,
         'trimmed_subject': trimmed_subject,
         'my_name':         my_name,
         'my_addr':         my_addr}
    r = MIMEText (t, 'plain', wleconfig.config.get ('DEFAULT', 'charset'))
    try: r['In-Reply-To'] = m.get ('message-id')
    except: pass
    rsubject = wlemail.make_answer (subject)
    r['Precedence'] = 'junk'
    rfrom = email.Utils.formataddr ((my_name, my_addr))
    wlelog.log (3, "Sending vacation message to %s" % target)
    wlemail.complete_message (r, rfrom, target, rsubject)
    wlemail.add_action (m, "Vacation message sent")
    return r

#
# Handle incoming message and send vacation message if appropriate
#
def handle_incoming (m):
    if not wleconfig.config.getboolean ('DEFAULT', 'vacation'): return
    if wlemail.from_mailinglist (m): return
    if wlemail.sent_by_myself (m): return
    if not wlemail.sent_to_me (m): return
    r = vacation_message (m)
    if r: wlemail.send_message (r)
