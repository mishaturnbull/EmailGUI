#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
EmailGUI.py provides a simple graphical interface designed to send an email.
It allows the user to login to their email and send email to exactly one
destination, from a specific SMTP server.

To import and use:
```
from EmailGUI import EmailerGUI
EmailerGUI()
```
Or simply run this file in Python, and the program will run.
"""

from __future__ import (division, print_function, generators, absolute_import)

# Misha Turnbull
# R020160506T0850
# EmailGUI.py

# backwards compatible - runs on python 2 or 3
# tested [successfully] on:
# - windows 10 (GUI, prompt, commandline, GUI multi-account, verification sub)
# - windows 7 (GUI)
# - osx el capitan (GUI)
# - kali linux 2106.1 (GUI)
# - kali linux 2106.2 (GUI)

# pylint: disable=W0511
# pylint yells at me for being organized and keeping track of goals -- it
# doesn't like TODO comments
# hrmph.  i shall not hear it.

# [DONE] TODO: nogui mode
# [DONE] TODO: delay factor in autoselect multithreading
# TODO: make help window scroll
# [DONE] TODO: allow multiple accounts to be used as senders
# TODO: custom SMTP server?
# TODO: command-line implementation (wip)
# [DONE] TODO: notify on completion
# [DONE] TODO: test multiple attachment sending
# [DONE] TODO: Email verification

# %% imports and constants

import argparse
import sys
import platform
import time
import smtplib
import subprocess
import os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders

# yeah, Tkinter imports are missing.
# they're conditionally imported in the function main() near the bottom
# of the program, so they aren't loaded if we run in nogui mode and they
# arent needed.

__version__ = '1.1'
__author__ = 'Misha Turnbull'
__author_email__ = 'blerghhh86@gmail.com'  # yes, really.  it's me.
__last_update__ = '20161210'

DEFAULT_FROM = 'blerghhh86@gmail.com, blerghhh87@gmail.com,\
 blerghhh88@gmail.com, blerghhh89@gmail.com'
DEFAULT_TO = ''
DEFAULT_SUBJECT = 'Apology'
DEFAULT_TEXT = """Dear recipient,
I am writing to apologize for incessantly writing you emails.  It must be
tiresome to spend all day deleting them.


P.S. Please forgive me for sending this email.  I shall immediately dispatch
a second email in apology."""
DEFAULT_SERVER = 'smtp.gmail.com:587'  # could also use port 465
DEFAULT_AMOUNT = '10'
DEFAULT_ATTACH = ''
DEFAULT_DELAY = '0'
DEFAULT_MULTITHREAD = None  # set this later, after suggest_thread_amt()
TITLE = 'SpamBotFromHell'
DEBUG = False
CONFIRMATION_MSG = """Are you certain you wish to proceed?
This cannot be undone and can have dangerous results!"""
LOG_STDOUT = 'Email_Log.out'
LOG_STDERR = 'Email_Log_Err.out'
MAX_RETRIES = 5
CON_PER = False

SMTP_RESPONSE_CODES = {
    200: "Nonstandard success response",
    211: "System status, or system help reply",
    214: "Help message",
    220: "<domain> Service ready",
    221: "<domain> Service closing transmission channel",
    250: "Requested mail action okay, completed",
    251: "User not local; will forward to <forward-path>",
    252: "Cannot VRFY user, but will accept message and attempt delivery",
    354: "Start mail input; end with <CRLF>.<CRLF>",
    421: "<doman> Service not available, closing transmission channel",
    450: "Requested mail action not taken: mailbox unavailable",
    451: "Requested action aborted: local error in processing",
    452: "Requested action not taken: insufficient system storage",
    500: "Syntax error, command unrecognized",
    501: "Syntax error in parameters or arguments",
    502: "Command not implemented",
    503: "Bad sequence of commands",
    504: "Command parameter not implemented",
    521: "<domain> does not accept mail",
    530: "Access denied",
    550: "Requested action not taken: mailbox unavailable",
    551: "User not local, please try <forward-path>",
    552: "Request mail action aborted: exceeded storage allocation",
    553: "Requested action not taken: mailbox name not allowed",
    554: "Transaction failed",
}
    

# %% Parse arguments

# pylint complains about invalid constant names, but I argue that "parser" and
# "args" aren't constants but are used as main script which must be created
# outside of a main() function

# i shan't hear it
# pylint: disable=C0103
parser = argparse.ArgumentParser(description="Send emails like a pro.",
                                 prefix_chars='/-',
                                 fromfile_prefix_chars='')
parser.add_argument('-p', '--nogui', dest='NOGUI', action='store_const',
                    const=True, default=False,
                    help='specify to run without a GUI')
parser.add_argument('-d', '--debug', dest='DEBUG', action='store_const',
                    const=True, default=False,
                    help='output program debugging info')
parser.add_argument('-c', '--commandline', dest='COMMANDLINE',
                    action='store_const', const=True, default=False,
                    help='pass parameters as arguments to command')
parser.add_argument('--amount', nargs=1, dest='AMOUNT',
                    type=int, required=False, default=DEFAULT_AMOUNT,
                    help='amount of emails to send')
parser.add_argument('--rcpt', nargs=1, dest='RCPT',
                    type=str, required=False, default=DEFAULT_TO,
                    help='unlucky recipient of emails')
parser.add_argument('--from', nargs=1, dest='FROM',
                    type=str, required=False, default=DEFAULT_FROM,
                    help='your (sender\'s) email address')
parser.add_argument('--pwd', nargs=1, dest='PASSWORD',
                    type=str, required=False,
                    help='your (sender\'s) email password')
parser.add_argument('--server', nargs=1, dest='SERVER',
                    type=str, required=False, default=DEFAULT_SERVER,
                    help='smtp server to send emails from')
parser.add_argument('--max-retries', nargs=1, dest='MAX_RETRIES',
                    type=int, required=False, default=MAX_RETRIES,
                    help='the maximum number of times the program will'
                         ' attempt to reconnect to the server if ocnnection'
                         ' is lost')
args = parser.parse_args()

if isinstance(args.AMOUNT, list):
    # this happens sometimes
    DEFAULT_AMOUNT = args.AMOUNT[0]
else:
    DEFAULT_AMOUNT = args.AMOUNT
DEFAULT_TO = args.RCPT
DEFAULT_FROM = args.FROM
DEFAULT_SERVER = args.SERVER
MAX_RETRIES = args.MAX_RETRIES
DEBUG = args.DEBUG
if not args.NOGUI:
    # pylint: disable=C0413
    #  we should only really import tkinter if we need it, it's a big
    #  module and some users may be on platforms that don't support it
    # if so, trying to import it will make things come to a quick halt so
    #  we only import it if we actually need it -- for a GUI
    if sys.version_info.major == 3:
        import tkinter as tk
        import tkinter.messagebox as messagebox
        import tkinter.filedialog as filedialog
    elif sys.version_info.major == 2:
        # pylint: disable=E0401
        # pylint complains about not finding tkMessageBox etc
        #  when run using python 3, because this stuff is for python 2
        #  but this block will never be executed in py3, and therefore
        #  will never throw an error
        import Tkinter as tk
        import tkMessageBox as messagebox
        import tkFileDialog as filedialog
    else:
        assert False, 'Sorry, I dunno what you\'re using but it\'s probably \
                       not something I designed this program to be used with.'

# %% conditional import/setup

# use xrange if python 2 to speed things up
# in py3, range is what xrange was
# and in python 2, use raw_input to prevent input()'s hack-ability
BEST_RANGE = range  # pylint: disable=C0103
BEST_INPUT = input  # pylint: disable=C0103
if sys.version_info.major == 2:
    # this will never throw a NameError in py3 because the condition above
    # is false, meaning this never executes
    BEST_RANGE = xrange  # pylint: disable=E0602
    BEST_INPUT = raw_input  # pylint: disable=E0602


class FakeSTDOUT(object):
    '''Pretend to be sys.stdout, but write everything to a log AND
    the actual sys.stdout.'''

    def __init__(self, stream, filename):
        self.terminal = stream
        self.log = open(filename, 'w')

    def write(self, message):
        '''Impersonate sys.stdout.write()'''
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        '''Impersonate sys.stdout.flush().  Needed for py3 compatibility.'''
        self.terminal.flush()

    def FSO_close(self):
        self.log.close()

sys.stdout = FakeSTDOUT(sys.stdout, LOG_STDOUT)
sys.stderr = FakeSTDOUT(sys.stderr, LOG_STDERR)


class EmailSendError(Exception):
    '''Exception class for exceptions raised within EmailGUI.'''
    pass

# these are the error classes that should raise a popup box presented to the
# user.  others either should never happen or should be silenced and handled
# internally.
POPUP_ERRORS = [smtplib.SMTPAuthenticationError,
                smtplib.SMTPDataError,
                EmailSendError]

# %% Tempfiles

# Multithreading is set up as follows:
#  In Limited mode (with #threads as mt_num):
#   1. mt_lim is formatted and written to tempEmail.py
#   2. mt_num new threads are spawned that each execute tempEmail.py
#   3. If any emails remain to be sent [1], they are launched from this thread
#  In Unlimited mode (with #emails as amount):
#   1. mt_ulim is formatted and written to tempEmail.py
#   2. amount new threads are spawned that each execute tempEmail.py

# [1]: This can happen when amount % mt_num != 0, for example 100 emails acros
#      15 threads. In this case, the threading autoselector will reduce
#      #threads by 1 to avoid SMTP 421


# this is the code that will be formatted and then written to a temporary file
# for multithreading
# unfortunately, the only way to pass the password on is to either pass via
# sys.argv (unencrypted) or put it directly in the file (unencrypted).  i chose
# to put it in the file given that the user of this program likely already
# knows his/her password, and wouldn't be very concerned about him/herself
# seeing it plain.
MT_ULIM = """
# -*- coding: utf-8 -*-
import smtplib
from threading import current_thread
import sys
ident = sys.argv[1]

serveraddress = '{server}'
From = '{From}'
to = '{to}'
password = '{password}'
message = \\
'''{message}
'''.format(thread=current_thread(), ident=ident)

server = smtplib.SMTP(serveraddress)
server.set_debuglevel(1)
server.ehlo_or_helo_if_needed()
server.starttls()
server.ehlo()
# not as worried about 421 disconnects here -- it would only affect one email
server.login(From, password)
server.sendmail(From, to, message)
server.quit()
"""

MT_LIM = """
import smtplib
from threading import current_thread
import sys
ident = sys.argv[1]

serveraddress = '{server}'
From = '{From}'
to = '{to}'
password = '{password}'
message = \\
'''{message}
'''

def main(num={num_emails}):
    server = smtplib.SMTP(serveraddress)
    server.set_debuglevel(1)
    server.ehlo_or_helo_if_needed()
    server.starttls()
    server.ehlo()
    server.login(From, password)
    try:
        for _ in range(num):
            server.sendmail(From, to, message.format(thread=current_thread(),
                                                     ident=ident,
                                                     num=_))
    except smtplib.SMTPServerDisconnected as exc:
        server.quit()
        main({num_emails} - _)
    finally:
        server.quit()
if __name__ == '__main__':
    main()
"""

GUI_DOC = """
A brief guide to using EmailGUI.py's GUI (Graphical User Interface).

Text entry fields:
    # emails: default {DEFAULT_AMOUNT}.  Specifies number of emails to send.
        Note that this is # emails PER OUTBOUND ACCOUNT, NOT TOTAL!
    Subject: default '{DEFAULT_SUBJECT}'.  Specifies the subject line of
        the emails.
    From: default '{DEFAULT_FROM}'.  Specifies your (the sender) email address.
        Multiple accounts are allowed, split with commas.
    Password: no default.  Specifies your email account password.
        Multiple passwords (for multiple accounts) are allowed, split with
        commas.
    To: default '{DEFAULT_TO}'.  Specifies the recipient's email address.
        The 'Verify' button at the left-hand side of the text bar will
        attempt to determine whether or not the specified address is valid.**
    Server: default '{DEFAULT_SERVER}'.  Specifies the server to use for SMTP.
        Multiple servers (for multiple accounts) are allowed, split with
        commas.
    Message text: default '{DEFAULT_TEXT}'.  Specifies message content.
    Attachments: default '{DEFAULT_ATTACH}'.  Specifies files to be attached.
                 The 'Browse' button at the left-hand side of the text
                 bar provides a file browser window for easy file selection.

Using multiple accounts:
    To send from multiple accounts, enter a list of the addresses to be used
    in the 'From' field, comma-separated.  Whitespace between commas and
    addresses is allowable.  If the accounts have different passwords and/or
    servers, those must be entered in parallel in the password field and/or the
    server field respectively.  If less passwords and/or servers are given than
    accounts, the remainder of from addresses will be paired with the LAST
    GIVEN password and/or server.  If less from accounts are given than either
    passwords or servers, the remainder of passwords and/or servers will be
    ignored.

    It should be noted that the '# emails' field represents the number of
    emails to be sent FROM EACH ACCOUNT.  It does NOT divide the number given
    into any amount between accounts.

Menus:
    Email:
        Send: Asks for confirmation, then sends the email[s] as configured.
        Auto-Select Threading: Given the number of emails to be sent,
                               automatically set the multithreading mode so
                               that it is A. most likely to succeed and B.
                               faster.
    Client:
        Cleanup: Erase any temporary files written by the program.
        Exit: Run cleanup, then exit the program.  Provides the same
              functionality as the 'X' (close) button.
        Exit without cleanup: Exit the program without cleaning up temp files.
        Write tempEmail.py: Write any necessary temporary files.

    Help: display this help information.

Multithreading:
    This program is capable of using multiple threads (multithreading) to send
    more than one email simultaneously.  There are 3 modes to do so:
        None [delay]: Do not use multithreading - simply send each email
                      from the main thread.  If [delay] is not 0, the program
                      will wait [delay] seconds between each email.
        Limited [num]: Use only [num] threads.  Each thread gets a certain
                       amount of emails to send, and any left over are
                       sent from the parent thread*.
        Unlimited: Spawn a new thread for each email to be sent.

    *: this can sometimes mean that the total number of threads is 1 more than
       specified in [num], since there are [num] threads spawned as well as
       the main thread still running.
    **: this is not guaranteed to return the correct value!!
""".format(DEFAULT_AMOUNT=DEFAULT_AMOUNT,
           DEFAULT_SUBJECT=DEFAULT_SUBJECT,
           DEFAULT_FROM=DEFAULT_FROM,
           DEFAULT_TO=DEFAULT_TO,
           DEFAULT_SERVER=DEFAULT_SERVER,
           DEFAULT_TEXT=DEFAULT_TEXT,
           DEFAULT_ATTACH=DEFAULT_ATTACH)


# %% Helper functions
def handler_button_help():
    '''Show the help dialog.'''
    messagebox.showinfo(title='EmailGUI Help', message=GUI_DOC)


def suggest_thread_amt(num_emails):
    '''Given a total number of emails to send `num_emails`, determine which
multithreading mode/settings would likely be the fastest and least likely to
fail.

Prioritizes likeliehood of success over speed.

Returns a tuple (mt_mode, mt_num):
    :str: mt_mode := one of ['none', 'lim', 'ulim']
    :int: mt_num := if mt_mode == 'none': one of [0, 180]
                    if mt_mode == 'lim': in range(1, 16)
                    if mt_mode == 'ulim': 0

Note that in the case mt_mode == 'none', mt_num actually does not indicate
the number of threads to use, but rather a delay factor for intentionally
slowing down the sending of emails.  This is done to prevent daily send
quota limits from kicking in (for example, Gmail only allows 500 emails to be
send in 24 hours.  Sending one email every 3 minutes (180 seconds) will prevent
emails being blocked by sending less than 500 emails in 24 hours).  However,
it's often more convient to shoot off 500 emails quickly then wait for tomorrow
so instead, for num_emails = 500, return ('none', 0).  Only for num_emails>500
will we return 180.
'''

    # gmail only allows 15 connections to be open at a time from one IP
    # address before it throws a 421 error.  this function should
    # never return a combination which would allow more than 15 active
    # connections to the server.

    if num_emails == 1:
        # just one email.  seriously, why use multithreading??
        return ('none', 0, False)

    elif num_emails <= 15:
        # only use unlimited if it won't throw 421 errors -- happens above 15
        return ('ulim', 0, False)

    elif 500 > num_emails > 15:
        # limited is our best bet here
        if (num_emails % 15) == 0:
            # the number of emails divides evenly by 15 - use 15 threads and
            # each one gets num_emails / 15 emails to send
            return ('lim', 15, False)
        else:
            # num_emails does not divide by 15.  trying to use 15 threads will
            # result in each one having a float value of emails to send, which
            # makes no sense:
            #
            # client: "I want to send 3.3 emails to Joe!"
            # server: "Wut"
            #
            # To avoid this, use 14 threads and send the remainder in the
            # parent (this one)
            return ('lim', 14, False)
    elif num_emails == 500:
        # send 500 emails, but send them in one shot -- often easier, as noted
        # in the docstring, to send 500 then wait for tomorrow
        return ('lim', 14, False)
    elif num_emails > 500:
        # gmail allows no more than 500 emails in 24 hours
        # by using a delay of 2.88 minutes (172.8 seconds), we can send 500
        # emails in exactly 24 hours, thereby never triggering gmail's
        # send quota limit
        #
        # we use 3 minutes (180 seconds) just to be sure that we don't trigger
        # anti-spam
        return ('none', 180, True)

DEFAULT_MULTITHREAD = suggest_thread_amt(int(DEFAULT_AMOUNT))


def cleanup():
    '''Clean up temporary files created by the program.'''
    try:
        os.remove('tempEmail.py')
    except OSError:
        # file does not exist, our job is done
        pass


def verify_to(address, serv):
    """Given an address and a server to use, send an SMTP VRFY command
    and return the result."""
    # import smtplib
    server = smtplib.SMTP(serv)
    resp = server.verify(address)
    return resp


def verify_to_email(address, serv, frm, pwd):
    """Given an address and a server to use, attempt to verify the address
    by sending mail to it."""
    # import smtplib
    server = smtplib.SMTP(serv)
    server.ehlo_or_helo_if_needed()
    server.starttls()
    server.ehlo()
    server.login(frm, pwd)
    server.mail(frm)
    resp = server.rcpt(address)
    server.quit()
    return resp


# %% class for sending emails
class EmailSender(object):
    '''Class to do the dirty work of sending emails.'''

    def __init__(self, **kwargs):
        self._options = kwargs
        self._check_config()

    ###################################
    # allow user to be lazy, and get things like EmailSender(...)['to']
    # also keeps number of attributes down to one -- internal dictionary
    # called self._options
    def __setitem__(self, key, value):
        self._options[key] = value

    def __contains__(self, key):
        return key in self._options

    def __getitem__(self, key):
        return self._options[key]
    # end lazy-user-ability
    ##################################

    def _check_config(self):
        '''Yell if something is or could be wrong in the future.'''
        necessary = ['From', 'to', 'subject', 'multithreading', 'password',
                     'amount', 'message', 'server']
        for attr in necessary:
            assert attr in self._options, 'EmailSender() missing ' + attr

    def build_message(self):
        '''Construct the MIME multipart message.'''
        msg = MIMEMultipart()
        msg['From'] = self['From']
        if isinstance(self['to'], list):
            msg['To'] = COMMASPACE.join(self['to'])
        else:
            msg['To'] = self['to']
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = self['subject']
        mt_mode = self['multithreading'][0]

        # conditionally append message numbering info based on multithreading
        # mode.  kinda ugly, but makes better output
        if mt_mode == 'none':
            # no multithreading - just use a counter
            part2 = '\n\nEmail {num} of ' + str(self['amount'])
            msg.attach(MIMEText(self['message'] + part2))

        elif mt_mode == 'lim':
            # limited multithreading - number the messages from each thread
            n_mail = str(int(self['amount']) // self['multithreading'][1])
            part2 = '\n\nEmail {num} of ' + n_mail + (' from thread {thread}'
                                                      '({ident})')
            msg.attach(MIMEText(self['message'] + part2))

        elif mt_mode == 'ulim':
            # unlimited multithreading - number the threads
            part2 = '\n\nEmail from {ident} on ulim'
            msg.attach(MIMEText(self['message'] + part2))

        # attachments
        for filename in self['attach']:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(open(filename, 'rb').read())
            encoders.encode_base64(part)  # modifies in-place.  magic.
            filepath = os.path.basename(filename)
            part.add_header('Content-Disposition',
                            'attachment; filename="{}"'.format(filepath))
            msg.attach(part)

        # save the message as an attribute
        self['MIMEMessage'] = msg

    def write_tempfile(self):
        '''Make a temporary file and write the program to it.'''
        mt_mode = self['multithreading'][0]

        if mt_mode == 'none':
            # multithreading not enabled - no file needed.  write it anyways,
            # though, because we were told to.
            with open('tempEmail.py', 'w') as tempfile:
                tempfile.write('pass')
            return 1

        elif mt_mode == 'lim':
            # limited multithreading
            # grab number of threads
            mt_num = self['multithreading'][1]
            # do math.  find out how many emails per thread
            num_emails = str(int(self['amount']) // mt_num)
            self._options['num_emails'] = num_emails

            # write the file
            with open('tempEmail.py', 'w') as tempfile:
                mime = self['MIMEMessage'].as_string()
                tempfile.write(MT_LIM.format(server=self['server'],
                                             From=self['From'],
                                             to=self['to'],
                                             password=self['password'],
                                             message=mime,
                                             num_emails=num_emails))
            return 1

        elif mt_mode == 'ulim':
            # unlimited multithreading.  write script for 1 email
            with open('tempEmail.py', 'w') as tempfile:
                mime = self['MIMEMessage'].as_string()
                tempfile.write(MT_ULIM.format(server=self['server'],
                                              From=self['From'],
                                              to=self['to'],
                                              password=self['password'],
                                              message=mime))
            return 1

    def _launch(self, nsend, _recur=0, delay=0):
        '''Send `nsend` emails.'''
        
        con_per = self['multithreading'][2]        
        
        def connect():
            if 'localhost' in self['server']:
                port = int(self['server'].split(':')[1])
                subprocess.Popen(["python", "-m smtpd", "-n", "-c",
                                  "DebuggingServer localhost:{}".format(port)])
                server = smtplib.SMTP('localhost', port)
            else:
                server = smtplib.SMTP(self['server'])
            if DEBUG:
                server.set_debuglevel(1)
            server.ehlo_or_helo_if_needed()
            server.starttls()
            server.ehlo()
            server.login(self['From'], self['password'])
            
            return server
        
        if not con_per:
            server = connect()

        # try to send the emails.
        # in the case of a 421 error, assume temp. issue and try again with the
        # rest of the emails to be sent.
        try:
            mime = self['MIMEMessage'].as_string()

            # this annoying if has to be here to make sure the email counter
            # works properly on m.t. modes none and lim.  on ulim, there is no
            # counter per say.
            if self['multithreading'][0] == 'none':
                for _ in BEST_RANGE(nsend):
                    if DEBUG:
                        print('Launching {} at ' .format(_) + str(time.time()))
                    
                    if con_per:
                        server = connect()
                    server.sendmail(self['From'], self['to'],
                                    mime.format(num=_ + 1))
                    time.sleep(int(delay))
            elif self['multithreading'][0] == 'lim':
                for _ in BEST_RANGE(nsend):
                    if DEBUG:
                        print('Launching {} at '.format(_) + str(time.time()))
                    if con_per:
                        server = connect()
                    server.sendmail(self['From'], self['to'], mime)

        except smtplib.SMTPServerDisconnected:
            # first, stop trying to connect to a dead server
            server.quit()
            # could happen if the internet goes out temporarily.  we just
            # try to resend and pray for the best
            sys.stderr.write('=== Server disconnected.  Trying again. ===')
            # use _recur to prevent recursion errors if the internet is out
            if _recur <= MAX_RETRIES:
                # send however many emails are left over
                self._launch(nsend - _, _recur=_recur + 1)
            else:
                # tried too many times, give up and make it the user's
                # problem
                raise

        finally:
            # everything died.  just give up.
            server.quit()

    def send(self):
        '''FIRE THE CANNONS!'''
        # make sure everything is ready
        self._check_config()
        self.build_message()
        if DEBUG:
            mime = self['MIMEMessage'].as_string()
            print("Launching {} copies: \n{}".format(self['amount'], mime))
        mt_mode = self['multithreading'][0]

        # no multithreading. simply launch emails.
        if mt_mode == 'none':
            self._launch(self['amount'], delay=self['delay'])

        # multithreading, yuck
        elif mt_mode in ['lim', 'ulim']:
            # either way we need a tempfile
            self.write_tempfile()

            # limited mode - only use mt_num threads (prevents errors)
            if mt_mode == 'lim':
                mt_num = self['multithreading'][1]
                # spawn the threads
                for _ in BEST_RANGE(int(self['multithreading'][1])):
                    print("New thread: {} emails".format(self['num_emails']))
                    subprocess.Popen([sys.executable, 'tempEmail.py', str(_)],
                                     stderr=subprocess.STDOUT)

                # sometimes the number of emails doesn't divide evenly by
                # mt_num, so we have to launch the remainder from here.
                # usually a small number so this is ok
                leftover = self['amount'] - (self['amount'] // mt_num) * mt_num
                print('{} leftovers'.format(leftover))
                self._launch(leftover)

            # unlimited mode - one thread for each email
            # often throws connectivity errors
            elif mt_mode == 'ulim':
                for _ in BEST_RANGE(self['amount']):
                    subprocess.Popen([sys.executable, 'tempEmail.py', str(_)],
                                     stderr=subprocess.STDOUT)
        return 1


# %% classes for user interface
class EmailPrompt(object):
    '''Prompt the user for information for emails, and send it.  Done via
    stdin/stdout.'''

    def __init__(self, _autorun=True):
        '''Make Stuff Happen'''
        self.server = self.amount = self.frm = self.delay = None
        self.multithreading = self.subject = self.files = self.text = None
        self._sender = self.rcpt = self.password = None

        if _autorun:
            self._run()

    def _make_sender(self, i=0):
        '''Create the EmailSender object for this email.'''
        print("EmailPrompt._make_sender: i = " + str(i))
        self._sender = EmailSender(server=self.server[i],
                                   From=self.frm[i],
                                   to=self.rcpt,
                                   message=self.text,
                                   subject=self.subject,
                                   multithreading=self.multithreading,
                                   attach=self.files,
                                   password=self.password[i],
                                   amount=self.amount,
                                   delay=self.delay)

    def send_msg(self):
        '''FIRE THE CANNONS!'''
        if DEBUG:
            print('Sending msg: \n{}\nfrom {} {} times'.format(self.text,
                                                               self.server,
                                                               self.amount))
        for i in BEST_RANGE(len(self.frm)):
            self._make_sender(i)
            self._sender.send()

    def make_tempfile(self):
        '''If necessary, use the EmailSender class to write a temporary
        file.'''
        self._make_sender()
        self._sender.build_message()
        self._sender.write_tempfile()

    def handler_automt(self):
        '''User wants us to automatically select multithreading settings -
        what to do?? call this function.  that's what.'''
        suggestion = suggest_thread_amt(int(self.amount))
        mt_mode, mt_num = suggestion
        if mt_mode == 'none':
            self.delay = mt_num
            self.multithreading = ('none', 0)
        elif mt_mode == 'lim':
            self.delay = 0
            self.multithreading = ('lim', suggestion[1])
        elif mt_mode == 'ulim':
            self.delay = 0
            self.multithreading = ('ulim', 0)

    def prompt_for_values(self):
        '''Ask the user what they want to do.'''
        print('Welcome to SpamBotFromHell! Please enter your desired'
              'configuration as prompted below.')
        self.amount = int(BEST_INPUT("Number of emails to send > "))
        self.rcpt = BEST_INPUT("Unlucky person's email address > ")
        self.frm = [a.strip() for a in
                    BEST_INPUT("Your email address > ").split(',')]
        self.password = [a.strip for a in
                         BEST_INPUT("Your email password > ").split(',')]
        self.server = [a.strip() for a in
                       BEST_INPUT("Server to send mail from > ").split(',')]
        self.subject = BEST_INPUT("Message subject > ")
        print("Enter message, end with ctrl+D:")
        self.text = ''
        while True:
            line = BEST_INPUT('')
            if not line:
                break
            self.text = self.text + line
        mt_mode = None
        while not (mt_mode in ['none', 'lim', 'ulim', 'auto']):
            print("\nMultithreading mode: enter one of 'none', 'limited', "
                  "'unlimited', or 'auto'.")
            inp = BEST_INPUT("> ").strip().lower()
            mt_mode = ['none', 'lim', 'ulim', 'auto'][['none',
                                                       'limited',
                                                       'unlimited',
                                                       'auto'].index(inp)]
        if mt_mode == 'none':
            self.delay = int(BEST_INPUT('Delay factor (seconds) > '))
            self.multithreading = ('none', 0)
        elif mt_mode == 'lim':
            mt_num = int(BEST_INPUT('Number of threads > '))
            self.multithreading = ('lim', mt_num)
        elif mt_mode == 'ulim':
            self.delay = 0
            self.multithreading = ('ulim', 0)
        elif mt_mode == 'auto':
            self.handler_automt()

        self.files = BEST_INPUT("Attachments > ")

    def _run(self):
        '''Here's the internal method magic that actually does stuff.'''
        self.prompt_for_values()
        self.send_msg()


class EmailerGUI(EmailPrompt):
    '''Make things easier to use, and prettier.'''

    def __init__(self):
        '''Start the class, and make stuff happen.'''
        EmailPrompt.__init__(self, _autorun=False)
        self.root = tk.Tk()
        self.init_gui()

        self.root.protocol('WM_DELETE_WINDOW', lambda: [cleanup(),
                                                        self.exit()])

        # self.root.mainloop needs to be called sometimes - but not always?
        # can't figure out a pattern here.
        if platform.system() in ['Linux', 'Darwin']:
            self.root.mainloop()
        if sys.version_info.major == 3 and platform.system() == 'Windows':
            self.root.mainloop()

    def exit(self):
        '''Close the window.  ***DOES NOT RUN CLEANUP***'''
        self.root.destroy()

    def handler_button_send(self):
        '''Handle the 'Send' button being clicked.
           Tries to send the message, but if it doesn't work spawns a
           popup saying why.'''

        # ask for confirmation
        if messagebox.askyesno(TITLE, CONFIRMATION_MSG):
            try:
                self.create_msg_config()
                # dear reader, you might be inclined to expect something like:
                # for i in BEST_RANGE(len(self.frm)):
                #    self.send_msg()
                # but this is not what you see.  instead, we just let
                # EmailPromp's .send_msg() handle the looping -- if we do it
                # here as well, the program sends exactly twice as many emails
                # as it should because it sends emails i times, i times.
                # therefore shouldn't loop here.
                self.send_msg()
            except smtplib.SMTPResponseException as exc:

                # pylint might yell here, about W1504:
                #
                # Using type() instead of isinstance() for a typecheck.
                #
                # in this case, to use isinstance(), we'd have to do something
                # with any(...) that would be way uglier than this.

                # C0123 is the same thing as W1504, but it's not W1504...
                # pylint: disable=C0123
                if type(exc) in POPUP_ERRORS:
                    messagebox.showerror(TITLE, exc.smtp_error)
            except smtplib.SMTPException as exc:
                # pylint: disable=C0123
                if type(exc) in POPUP_ERRORS:
                    messagebox.showerror(TITLE, exc.args[0])

            # we're done here, notify the user that it's safe to exit
            # This is okay on multithreading modes because exiting this
            # thread shouldn't kill it's spawned processesß
            messagebox.showinfo("Done!", "Done!")

    def handler_automt(self):
        '''Handle the 'Auto-select Threading' button.
           Checks with the function suggest_thread_amt() using the specified
           number of emails, then sets multithreading mode accordingly.'''

        suggestion = suggest_thread_amt(int(self.entry_amount.get()))
        self.query_multithreading.set(suggestion[0])  # set the mode
        self.query_conmode.set(suggestion[2])

        # if limited, set num. threads
        if suggestion[0] == 'lim':
            self.n_threads.delete(0, 'end')  # clear field
            self.n_threads.insert(0, str(suggestion[1]))  # insert suggestion

        # if no multithreading, set delay
        elif suggestion[0] == 'none':
            self.entry_delay.delete(0, 'end')  # clear field
            self.entry_delay.insert(0, str(suggestion[1]))  # insert suggestion

    def create_msg_config(self):
        '''Create the necessary attributes to create a message.
           Raises EmailSendError if something important is missing.'''
        self.server = self.entry_server.get()
        self.frm = self.entry_from.get()
        self.password = self.entry_password.get() or args.PASSWORD
        self.text = self.entry_text.get()
        self.subject = self.entry_subject.get()
        self.amount = int(self.entry_amount.get())
        self.rcpt = self.entry_to.get()
        mt_mode = self.query_multithreading.get()
        mt_num = int(self.n_threads.get())
        conmode = self.query_conmode.get()
        self.multithreading = (mt_mode, mt_num, conmode)
        self.files = self.file_entry.get().split(',')
        delay = self.entry_delay.get()
        if delay == '':
            self.delay = 0
        else:
            self.delay = delay
        if self.files == ['']:
            self.files = []
        MAX_RETRIES = int(self.entry_retry.get())
        if not all([bool(x) for x in [self.server, self.frm, self.text,
                                      self.subject, self.amount, self.rcpt]]):
            raise EmailSendError("One or more required fields left blank!")
        self.split_accounts()  # split server, frm, password into lists

    def split_accounts(self):
        '''Take the user-given values for .frm, .password and .server
        and split them on commas (and strip whitespace).  If the lists are of
        unequal length, sort that out too.'''
        self.server = [a.strip() for a in self.server.split(',')]
        self.frm = [a.strip() for a in self.frm.split(',')]
        self.password = [a.strip() for a in self.password.split(',')]

        # we want the lists to have the same length as self.frm -- the user
        # could have 2 or more accounts with the same address and server
        # this way, we assume if less passwords and/or servers are given
        # that we populate the rest of the lists with clones of the last given
        # password/server.
        if len(self.server) < len(self.frm):
            self.server += [self.server[-1]] * (len(self.frm) -
                                                len(self.server))
        if len(self.password) < len(self.frm):
            self.password += [self.password[-1]] * (len(self.frm) -
                                                    len(self.password))

    def _make_sender(self, i=0):
        self.create_msg_config()
        EmailPrompt._make_sender(self, i)

    def check_retcode(self):
        def lookup_code():
            retcode = int(entry_resp.get())
            if retcode not in SMTP_RESPONSE_CODES:
                msg = "Sorry, I don't know that one!"
            else:
                msg = SMTP_RESPONSE_CODES[retcode]
            label_code.config(text=msg)
        
        retmen = tk.Toplevel(self.root)
        retmen.wm_title("Response codes")
        label_resp = tk.Label(retmen, text="Response code: ")
        label_resp.grid(row=0, column=0, sticky=tk.W)
        entry_resp = tk.Entry(retmen, width=4)
        entry_resp.grid(row=0, column=1, sticky=tk.W)
        label_err = tk.Label(retmen, text="Error: ")
        label_err.grid(row=1, column=0, sticky=tk.W)
        label_code = tk.Label(retmen, text=(' ' * 62))
        label_code.grid(row=1, column=1, sticky=tk.W);
        button_lookup = tk.Button(retmen, text='Look up', command=lookup_code)
        button_lookup.grid(row=3, column=0, sticky=tk.W)
        

    def verify_to(self):
        """Verify the email address the user wants to send to and show
        a message box containing the result.  Graphical mode only."""
        def VRFY():
            '''Button handler for verify mode using SMTP VRFY verb.'''
            serv = self.entry_server.get() or DEFAULT_SERVER
            label_VRFY_res.config(text=' ')
            resp = verify_to(entry_to.get(), serv)
            c = resp[0]
            if c == 250:
                msg = str(c) + " Email appears valid."
            elif c == 251:
                msg = str(c) + " Email appears forwarded."
            elif c == 252:
                msg = str(c) + " Server could not determine."
            else:
                msg = str(c) + "Address either invalid or unable to determine."
            label_VRFY_res.config(text=msg)

        def MAIL():
            '''Button handler for verify mode using email test.'''
            serv = self.entry_server.get() or DEFAULT_SERVER
            label_MAIL_res.config(text=' ')
            resp = verify_to_email(entry_to.get(),
                                   serv,
                                   entry_from.get(),
                                   entry_password.get())
            c = resp[0]
            if c == 550:
                msg = str(c) + " Email appears invalid."
            elif c == 250:
                msg = str(c) + " Email appears valid."
            else:
                msg = str(c) + " Could not determine."
            label_MAIL_res.config(text=msg)

        def paste_addr():
            '''Button handler for paste address into main window.'''
            self.entry_to.delete(0, len(self.entry_to.get()))
            self.entry_to.insert(0, entry_to.get())

        def paste_serv():
            '''Button handler for paste server into main window.'''
            self.entry_server.delete(0, len(self.entry_server.get()))
            self.entry_server.insert(0, entry_serv.get())

        vrfymen = tk.Toplevel(self.root)
        vrfymen.wm_title("Verification")
        label_from = tk.Label(vrfymen, text='Verify from:')
        label_from.grid(row=0, column=0, sticky=tk.W)
        entry_from = tk.Entry(vrfymen, width=40)
        entry_from.grid(row=0, column=1, columnspan=2, sticky=tk.W)
        entry_from.insert(0, DEFAULT_FROM.split(',')[0])
        label_password = tk.Label(vrfymen, text='Verify password:')
        label_password.grid(row=1, column=0, sticky=tk.W)
        entry_password = tk.Entry(vrfymen, width=40, show='*')
        entry_password.grid(row=1, column=1, columnspan=2, sticky=tk.W)
        entry_password.insert(0, self.entry_password.get())
        label_to = tk.Label(vrfymen, text='To:')
        label_to.grid(row=2, column=0, sticky=tk.W)
        entry_to = tk.Entry(vrfymen, width=40)
        entry_to.grid(row=2, column=1, columnspan=2, sticky=tk.W)
        entry_to.insert(0, self.entry_to.get())
        label_serv = tk.Label(vrfymen, text="Server:")
        label_serv.grid(row=3, column=0, sticky=tk.W)
        entry_serv = tk.Entry(vrfymen, width=40)
        entry_serv.grid(row=3, column=1, columnspan=2, sticky=tk.W)
        entry_serv.insert(0, self.entry_server.get())
        button_VRFY = tk.Button(vrfymen, text="VRFY", command=VRFY)
        button_VRFY.grid(row=4, column=0, sticky=tk.W)
        label_VRFY_res = tk.Label(vrfymen, text="")
        label_VRFY_res.grid(row=4, column=1, sticky=tk.W)
        button_MAIL = tk.Button(vrfymen, text="MAIL", command=MAIL)
        button_MAIL.grid(row=5, column=0, sticky=tk.W)
        label_MAIL_res = tk.Label(vrfymen, text="")
        label_MAIL_res.grid(row=5, column=1, sticky=tk.W)
        button_paste_addr = tk.Button(vrfymen, text="Paste address",
                                      command=paste_addr)
        button_paste_addr.grid(row=6, column=0, sticky=tk.W)
        button_paste_serv = tk.Button(vrfymen, text="Paste server",
                                      command=paste_serv)
        button_paste_serv.grid(row=6, column=1, sticky=tk.W)

    def init_gui(self):
        '''Build that ugly GUI.'''
        # ws = int(self.root.winfo_screenwidth() / 2)
        # hs = int(self.root.winfo_screenheight() / 2)
        self.root.title(TITLE)

        # if the length of DEFAULT_TEXT is greather than 180, use 180 as the
        # limit of the window width.  prevents window being wider than the
        # screen on smaller screens (laptops)
        width = min([len(DEFAULT_TEXT), 100])

        # number to send
        self.label_amount = tk.Label(self.root, text='# emails: ')
        self.label_amount.grid(row=1, column=0, sticky=tk.W)
        self.entry_amount = tk.Entry(self.root, width=5)
        self.entry_amount.grid(row=1, column=1, sticky=tk.W)
        self.entry_amount.insert(0, DEFAULT_AMOUNT)

        # subject
        self.label_subject = tk.Label(self.root, text='Subject: ')
        self.label_subject.grid(row=2, column=0, sticky=tk.W)
        self.entry_subject = tk.Entry(self.root, width=width)
        self.entry_subject.grid(row=2, column=1, columnspan=9,
                                sticky=tk.W + tk.E)
        self.entry_subject.insert(0, DEFAULT_SUBJECT)

        # text
        self.label_text = tk.Label(self.root, text='Message text: ')
        self.label_text.grid(row=7, column=0, sticky=tk.W)
        self.entry_text = tk.Entry(self.root, width=width)
        self.entry_text.grid(row=7, column=1, columnspan=9, sticky=tk.W + tk.E)
        self.entry_text.insert(0, DEFAULT_TEXT)

        # from
        self.label_from = tk.Label(self.root, text='From: ')
        self.label_from.grid(row=3, column=0, sticky=tk.W)
        self.entry_from = tk.Entry(self.root, width=width)
        self.entry_from.grid(row=3, column=1, columnspan=9, sticky=tk.W + tk.E)
        self.entry_from.insert(0, DEFAULT_FROM)

        # from password
        self.label_password = tk.Label(self.root, text='Password: ')
        self.label_password.grid(row=4, column=0, sticky=tk.W)
        self.entry_password = tk.Entry(self.root, show='*',
                                       width=width)
        self.entry_password.grid(row=4, column=1, columnspan=9,
                                 sticky=tk.W + tk.E)
        # only allow default passwords if the user specified one
        # otherwise set it to none
        self.entry_password.insert(0, args.PASSWORD or '')

        # to
        self.label_to = tk.Label(self.root, text='To: ')
        self.label_to.grid(row=5, column=0, sticky=tk.W)
        self.entry_to = tk.Entry(self.root, width=width)
        self.entry_to.grid(row=5, column=2, columnspan=8)
        self.entry_to.insert(0, DEFAULT_TO)

        # check email
        self.button_vrfy = tk.Button(self.root, text='Verify',
                                     command=self.verify_to)
        self.button_vrfy.grid(row=5, column=1)

        # server
        self.label_server = tk.Label(self.root, text='Server: ')
        self.label_server.grid(row=6, column=0, sticky=tk.W)
        self.entry_server = tk.Entry(self.root, width=width)
        self.entry_server.grid(row=6, column=1, columnspan=9,
                               sticky=tk.W + tk.E)
        self.entry_server.insert(0, DEFAULT_SERVER)

        # multithreading
        self.multithread_label = tk.Label(self.root,
                                          text='Multithreading mode:')
        self.multithread_label.grid(row=9, column=0, sticky=tk.W)
        self.query_multithreading = tk.StringVar()
        self.query_multithreading.set(DEFAULT_MULTITHREAD[0])
        self.mt_none = tk.Radiobutton(self.root, text='None',
                                      variable=self.query_multithreading,
                                      value='none')
        self.mt_lim = tk.Radiobutton(self.root, text='Limited: ',
                                     variable=self.query_multithreading,
                                     value='lim')
        self.mt_ulim = tk.Radiobutton(self.root, text='Unlimited',
                                      variable=self.query_multithreading,
                                      value='ulim')
        self.mt_none.grid(row=10, column=0, sticky=tk.W)
        self.mt_lim.grid(row=11, column=0, sticky=tk.W)
        self.mt_ulim.grid(row=12, column=0, sticky=tk.W)
        self.n_threads = tk.Entry(self.root, width=3)
        self.n_threads.insert(0, DEFAULT_MULTITHREAD[1])
        self.n_threads.grid(row=11, column=1, sticky=tk.W)

        # file attachments
        self.file_label = tk.Label(self.root, text='Attachments: ')
        self.file_label.grid(row=8, column=0, sticky=tk.W)
        self.file_entry = tk.Entry(self.root, width=width)
        self.file_entry.grid(row=8, column=2, columnspan=8)
        self.file_entry.insert(0, DEFAULT_ATTACH)
        # server options label
        self.opt_label1 = tk.Label(self.root, text='Server options:')
        self.opt_label1.grid(row=9, column=2, sticky=tk.W)        
        
        # max server retry attempts
        self.label_retry = tk.Label(self.root, text='Max. Retries: ')
        self.label_retry.grid(row=10, column=2, sticky=tk.W)
        self.entry_retry = tk.Entry(self.root, width=3)
        self.entry_retry.insert(0, str(MAX_RETRIES))
        self.entry_retry.grid(row=10, column=3, sticky=tk.W)
        
        # connect once or per email
        self.query_conmode = tk.BooleanVar()
        self.query_conmode.set(False)
        self.con_once = tk.Radiobutton(self.root, text='Connect once',
                                       variable=self.query_conmode,
                                       value=False)
        self.con_per = tk.Radiobutton(self.root, text='Connect per send',
                                      variable = self.query_conmode,
                                      value=True)
        self.con_once.grid(row=11, column=2, sticky=tk.W)
        self.con_per.grid(row=12, column=2, sticky=tk.W)
        

        def browse_file():
            '''Helper to display a file picker and insert the result in the
            file_entry field.'''
            filename = filedialog.askopenfilename()
            if self.file_entry.get() != '':
                self.file_entry.insert(0, filename + ",")
            else:
                self.file_entry.delete(0, 'end')
                self.file_entry.insert(0, filename)

        self.button_filebrowse = tk.Button(self.root, text='Browse',
                                           command=browse_file)
        self.button_filebrowse.grid(row=8, column=1)

        # Options
        self.menu_top = tk.Menu(self.root)
        self.menu_email = tk.Menu(self.menu_top, tearoff=0)
        self.menu_email.add_command(label='Send',
                                    command=self.handler_button_send)
        self.menu_email.add_command(label='Auto-Select Threading',
                                    command=self.handler_automt)
        self.menu_top.add_cascade(label='Email', menu=self.menu_email)

        self.menu_clientside = tk.Menu(self.menu_top, tearoff=0)
        self.menu_clientside.add_command(label='Cleanup', command=cleanup)
        self.menu_clientside.add_command(label='Exit', command=self.exit)
        self.menu_clientside.add_command(label='Exit without cleanup',
                                         command=self.root.destroy)
        self.menu_clientside.add_command(label='Write tempEmail.py',
                                         command=self.make_tempfile)
        self.menu_top.add_cascade(label='Client', menu=self.menu_clientside)

        self.menu_help = tk.Menu(self.menu_top, tearoff=0)
        self.menu_help.add_command(label='Documentation', command=handler_button_help)
        self.menu_help.add_command(label='SMTP Response code lookup',
                                   command=self.check_retcode)
        self.menu_top.add_cascade(label='Help', menu=self.menu_help)
        
        self.root.config(menu=self.menu_top)

        self.entry_delay = tk.Entry(self.root, width=3)
        self.entry_delay.grid(row=10, column=1, sticky=tk.W)
        self.entry_delay.insert(0, DEFAULT_DELAY)

        # label debug mode if it is on
        if DEBUG:
            label_debug = tk.Label(self.root, text='DEBUG')
            label_debug.grid(row=0, column=0)


# %% main
if __name__ == '__main__':
    try:
        # DO STUFF!
        if not args.NOGUI:
            EmailerGUI()
        elif args.NOGUI:
            EmailPrompt()
        elif args.COMMANDLINE:
            p = EmailPrompt(_autorun=False)
            p.send_msg()
    except KeyboardInterrupt as exc:
        sys.stdout.FSO_close()
        sys.stderr.FSO_close()
