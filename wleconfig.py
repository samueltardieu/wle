#
# $Id$
#
# WLE configuration file
#

import ConfigParser, os.path

_default_config = \
   { 'wledir':              os.path.expanduser ('~/.wle'),
     'whitelist':           '%(wledir)s/whitelist.txt',
     'ignorelist':          '%(wledir)s/ignorelist.txt',
     'confirmedlist':       '%(wledir)s/authorizedlist.txt',
     'queuedir':            '%(wledir)s/queue',
     'lockfile':            '%(wledir)s/lock',
     'languages':           'en',
     'templatesdir':        '%(wledir)s/templates',
     'myaddresses':         'NONE',
     'myname':              'NONE',
     'charset':             'iso-8859-1',
     'sendmail':            '/usr/sbin/sendmail',
     'secret':              'This is not so secret',
     'magic':               'Some magic string',
     'mailbox':             '/var/mail/%s' % os.environ['LOGNAME'],
     'junkbox':             os.path.expanduser ('~/Junk'),
     'bulkbox':             os.path.expanduser ('~/Bulk'),
     'confirmedbox':        os.path.expanduser ('~/Confirmed'),
     'people_add_other':    'no',
     'discuss_add_other':   'yes',
     'list_add_other':      'no',
     'allow_confirmer':     'yes',
     'confirm_recipients':  'yes',
     'max_confirm':         'yes',
     'logfile':             '%(wledir)s/log',
     'loglevel':            '0',
     'remove_days':         '10',
     'auto_delete_bounce':  'no',
     'magic_add_sender':    'yes',
     'dbdir':               '%(wledir)s/dbs',
     'old_requests':        '%(dbdir)s/old_requests',
     'confirmations':       '%(dbdir)s/confirmations',
     'confirmeddb':         '%(dbdir)s/authorized.sqlite',
     'dbname':              '%(wledir)s/wle.sqlite',
     'minimum_delay_hours': '6',
     'cleanup_days':        '10',
     'vacation':            'no',
     'vacation_msg':        '%(templatesdir)s/vacation.txt',
     'vacation_days':       '14',
     'vacation_db':         '%(dbdir)s/vacation',
     'statsdir':            '%(wledir)s/stats',
     'stats_received':      'no',
     'stats_confirmed':     'no',
     'stats_rejected':      'no',
     'stats_junk':          'no',
     'stats_bulk':          'no',
     'stats_authorized':    'no',
     'stats_delivered':     'no',
     'stats_queued':        'no'
   }

def read_config ():
    global config
    config = ConfigParser.ConfigParser(_default_config)
    config.read ([os.path.expanduser ('~/.wlerc')])

