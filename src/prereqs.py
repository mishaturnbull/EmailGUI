#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Handles configuration, imports, and conditional imports for the entire
module.
"""

from __future__ import (division, print_function, generators, absolute_import)

import sys
import json
import smtplib
import os

if sys.version_info.major == 3:
    # use xrange if python 2 to speed things up
    # in py3, range is what xrange was
    # and in python 2, use raw_input to prevent input()'s hack-ability
    BEST_RANGE = range  # pylint: disable=C0103
    BEST_INPUT = input  # pylint: disable=C0103
    FILE_NOT_FOUND = FileNotFoundError
elif sys.version_info.major == 2:
    # this will never throw a NameError in py3 because the condition above
    # is false, meaning this never executes
    BEST_RANGE = xrange  # pylint: disable=E0602
    BEST_INPUT = raw_input  # pylint: disable=E0602
    FILE_NOT_FOUND = IOError
else:
    raise RuntimeError("This code is not designed to be run outside of Python"
                       " 2 or 3!  Contact developer to fix this issue.")

try:
    with open("settings.json", 'r') as config:
        CONFIG = json.load(config)
except FILE_NOT_FOUND:
    sys.stderr.write("Couldn't find config file [settings.json]!")
    sys.exit(0)


# We need to join the message on newlines because it's stored in JSON
# as an array of strings
CONFIG['contents']['text'] = '\n'.join(CONFIG['contents']['text'])

MAX_RESP_LEN = max([len(CONFIG['SMTP_resp_codes'][i]) for i in
                    CONFIG['SMTP_resp_codes']])

#if isinstance(args.AMOUNT, list):
#    # this happens sometimes
#    CONFIG['settings']['amount'] = args.AMOUNT[0]
#else:
#    CONFIG['settings']['amount'] = args.AMOUNT
#CONFIG['contents']['to'] = args.RCPT
#CONFIG['contents']['from'] = args.FROM
#CONFIG['settings']['server'] = args.SERVER
#CONFIG['settings']['max_retries'] = args.MAX_RETRIES
#CONFIG['settings']['debug'] = args.DEBUG or CONFIG['settings']['debug']


if CONFIG['settings']['debug']:
    # we don't want to catch exceptions here -- let them fall, and get
    # a full & proper traceback
    class NeverGonnaHappenException(Exception):
        pass
    CATCH_EXC = NeverGonnaHappenException
else:
    CATCH_EXC = Exception


class FakeSTDOUT(object):
    '''Pretend to be sys.stdout, but write everything to a log AND
    the actual sys.stdout.'''

    def __init__(self, stream, filename, realtime=False):
        self.terminal = stream
        if not realtime:
            self.log = open(filename, 'w')
        self._filename = filename
        self.realtime = realtime

        self.is_empty = True

        self.write("\n----- starting log file -----\n", True)
        self.is_empty = True

    def write(self, message, logonly=False):
        '''Impersonate sys.stdout.write()'''
        if not logonly:
            self.terminal.write(message)

        if self.realtime:
            with open(self._filename, 'a') as log:
                log.write(message)
        else:
            self.log.write(message)

        self.is_empty = False

    def flush(self):
        '''Impersonate sys.stdout.flush().  Needed for py3 compatibility.'''
        self.terminal.flush()

    def dump_logs(self):
        """Dump log info already obtained, if any."""
        if not self.is_empty:
            self.log.close()
            self.log = open(self._filename, 'a')

    def FSO_close(self):
        '''Close the log files.'''
        empty = self.is_empty
        self.write("\n----- ending log file -----\n", True)
        self.is_empty = empty
        if not self.realtime:
            self.log.close()

        if not self.is_empty and not CONFIG['settings']['debug']:
            os.remove(self._filename)

        return self.terminal


class EmailSendError(Exception):
    '''Exception class for exceptions raised within EmailGUI.'''
    pass


class EmergencyStop(Exception):
    '''Specifically to be raised when the abort button is pressed.'''
    pass


# these are the error classes that should raise a popup box presented to the
# user.  others either should never happen or should be silenced and handled
# internally.
POPUP_ERRORS = [smtplib.SMTPAuthenticationError,
                smtplib.SMTPDataError,
                EmailSendError]

try:
    with open("GUI_DOC.template", 'r') as template:
        GUI_DOC = template.read().format(AMOUNT=CONFIG['settings']['amount'],
                                         SUBJECT=CONFIG['contents']['subject'],
                                         FROM=CONFIG['contents']['account'],
                                         TO=CONFIG['contents']['to'],
                                         SERVER=CONFIG['settings']['server'],
                                         TEXT=CONFIG['contents']['text'],
                                         ATTACH=CONFIG['contents']['attach'])

    with open("validation.regex", 'r') as regexfile:
        lines = regexfile.readlines()
        VALIDATION_RE = ''
        for line in lines:
            VALIDATION_RE += line.strip()

except FILE_NOT_FOUND as exc:
    print("Couldn't find necessary template file" +
          " [{}]".format(exc.filename), file=sys.stderr)
    sys.exit(0)
