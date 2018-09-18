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

# %% imports and constants

import argparse
import sys
import platform
import time
import smtplib
import os
import json
import threading
import copy
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders

# yeah, Tkinter imports are missing.
# they're conditionally imported in the conditional imports section further
# down after the arguments  so they aren't loaded if we run in nogui mode and
# they arent needed.

# %% config

if sys.version_info.major == 3:
    # use xrange if python 2 to speed things up
    # in py3, range is what xrange was
    # and in python 2, use raw_input to prevent input()'s hack-ability
    BEST_RANGE = range  # pylint: disable=C0103
    BEST_INPUT = input  # pylint: disable=C0103
    FILE_NOT_FOUND = FileNotFoundError
if sys.version_info.major == 2:
    # this will never throw a NameError in py3 because the condition above
    # is false, meaning this never executes
    BEST_RANGE = xrange  # pylint: disable=E0602
    BEST_INPUT = raw_input  # pylint: disable=E0602
    FILE_NOT_FOUND = IOError

try:
    with open("settings.json", 'r') as config:
        CONFIG = json.load(config)
except FILE_NOT_FOUND:
    sys.stderr.write("Couldn't find config file [settings.json]!")
    sys.exit(0)

# We need to join the message on newlines because it's stored in JSON
# as an array of strings
CONFIG['text'] = '\n'.join(CONFIG['text'])

# the SMTP response codes are indexed as strings due to JSON storage
# requirements, so change those to integers
for s in CONFIG['SMTP_resp_codes']:
    CONFIG['SMTP_resp_codes'].update({int(s):
                                      CONFIG['SMTP_resp_codes'].pop(s)})

MAX_RESP_LEN = max([len(CONFIG['SMTP_resp_codes'][i]) for i in
                    CONFIG['SMTP_resp_codes']])


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
                    type=int, required=False, default=CONFIG['amount'],
                    help='amount of emails to send')
parser.add_argument('--rcpt', nargs=1, dest='RCPT',
                    type=str, required=False, default=CONFIG['to'],
                    help='unlucky recipient of emails')
parser.add_argument('--from', nargs=1, dest='FROM',
                    type=str, required=False, default=CONFIG['from'],
                    help='your (sender\'s) email address')
parser.add_argument('--pwd', nargs=1, dest='PASSWORD',
                    type=str, required=False,
                    help='your (sender\'s) email password')
parser.add_argument('--server', nargs=1, dest='SERVER',
                    type=str, required=False, default=CONFIG['server'],
                    help='smtp server to send emails from')
parser.add_argument('--max-retries', nargs=1, dest='MAX_RETRIES',
                    type=int, required=False, default=CONFIG['max_retries'],
                    help='the maximum number of times the program will'
                         ' attempt to reconnect to the server if ocnnection'
                         ' is lost')
args = parser.parse_args()

if isinstance(args.AMOUNT, list):
    # this happens sometimes
    CONFIG['amount'] = args.AMOUNT[0]
else:
    CONFIG['amount'] = args.AMOUNT
CONFIG['to'] = args.RCPT
CONFIG['from'] = args.FROM
CONFIG['server'] = args.SERVER
CONFIG['max_retries'] = args.MAX_RETRIES
CONFIG['debug'] = args.DEBUG or CONFIG['debug']

# %% conditional import/setup

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
        import tkinter.scrolledtext as scrolledtext
        from tkinter import ttk
    elif sys.version_info.major == 2:
        # pylint: disable=E0401
        # pylint complains about not finding tkMessageBox etc
        #  when run using python 3, because this stuff is for python 2
        #  but this block will never be executed in py3, and therefore
        #  will never throw an error
        import Tkinter as tk
        import tkMessageBox as messagebox
        import tkFileDialog as filedialog
        import ScrolledText as scrolledtext
        import ttk
    else:
        assert False, 'Sorry, I dunno what you\'re using but it\'s probably \
                       not something I designed this program to be used with.'


class FakeSTDOUT(object):
    '''Pretend to be sys.stdout, but write everything to a log AND
    the actual sys.stdout.'''

    def __init__(self, stream, filename):
        self.terminal = stream
        self.log = open(filename, 'w')
        self._filename = filename

        self.is_empty = True

    def write(self, message):
        '''Impersonate sys.stdout.write()'''
        self.terminal.write(message)
        self.log.write(message)

        self.is_empty = False

    def flush(self):
        '''Impersonate sys.stdout.flush().  Needed for py3 compatibility.'''
        self.terminal.flush()

    def FSO_close(self):
        '''Close the log files.'''
        self.log.close()

        if not self.is_empty and not CONFIG['debug']:
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

# %% Tempfiles

try:

    with open("GUI_DOC.template", 'r') as template:
        GUI_DOC = template.read().format(AMOUNT=CONFIG['amount'],
                                         SUBJECT=CONFIG['subject'],
                                         FROM=CONFIG['from'],
                                         TO=CONFIG['to'],
                                         SERVER=CONFIG['server'],
                                         TEXT=CONFIG['text'],
                                         ATTACH=CONFIG['attach'])

except FILE_NOT_FOUND as exc:
    sys.stderr.write("Couldn't find necessary template file" +
                     " [{}]".format(exc.filename))
    sys.exit(0)


# %% Helper functions

def suggest_thread_amt(num_emails):
    '''Given a total number of emails to send `num_emails`, determine which
multithreading mode/settings would likely be the fastest and least likely to
fail.

Prioritizes likeliehood of success over speed.

Returns a tuple (mt_mode, mt_num, con_per):
    :str: mt_mode := one of ['none', 'lim', 'ulim']
    :int: mt_num := if mt_mode == 'none': one of [0, 180]
                    if mt_mode == 'lim': in range(1, 16)
                    if mt_mode == 'ulim': 0
    :bool: con_per := whether or not a connection should be established
                      for each email

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
            # To avoid this, use 14 threads with the same amount and send
            # the remainder in a 15th
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


CONFIG['multithread'] = suggest_thread_amt(int(CONFIG['amount']))


def verify_to(address, serv):
    """Given an address and a server to use, send an SMTP VRFY command
    and return the result."""
    # import smtplib
    server = smtplib.SMTP(serv)
    resp = server.verify(address)
    server.quit()
    return resp


def verify_to_email(address, serv, frm, pwd):
    """Given an address and a server to use, attempt to verify the address
    by sending mail to it."""
    # import smtplib
    server = smtplib.SMTP(serv)
    server.ehlo_or_helo_if_needed()
    if server.has_extn("STARTTLS"):
        server.starttls()
        server.ehlo()
    if server.has_extn("AUTH"):
        server.login(frm, pwd)
    server.mail(frm)
    resp = server.rcpt(address)
    server.quit()
    return resp


# %% multithreading!
class EmailSendHandler(threading.Thread):
    '''Handle a group of EmailSender classes.'''

    def __init__(self, bar_update_handle, **kwargs):
        super(EmailSendHandler, self).__init__()
        self._handler = bar_update_handle

        self._options = kwargs
        self._check_config()

        if self._handler is not None:
            self._handler.progress_bar["maximum"] = self["amount"]

        self.do_abort = False
        self.is_done = False

        self.n_sent = 0

        self._threads = []

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
            assert attr in self._options, 'EmailSendHandler() missing ' + attr

    def _final_check(self):
        '''Make sure everything is right in one final last-minute data
        validation check.

        At the time this method is called, it assumes that
        .generate_send_threads() has already been called and generated
        the worker threads.'''

        total_emails = 0
        for sender in self._threads:
            total_emails += sender["amount"]
            EmailSendHandler._check_config(sender)

        if total_emails != self["amount"]:
            raise EmergencyStop("Number of emails about to be sent does "
                                "not match number of emails requested!")

        if CONFIG['debug']:
            print("EmailSendHandler final check completed successfully")

    def generate_send_threads(self):
        '''Make a list of threads containing the threads to be run in their
        necessary configuration.'''
        mt_mode = self['multithreading'][0]

        # easiest case first.  If using unlimited threading mode, then simply
        # spawn <amount of emails> threads that send 1 email each.
        if mt_mode == 'ulim':
            n_threads = self['amount']
            n_emails_per_thread = 1

        # if we're on limited mode, then we need to spawn n amount of threads
        # with a certain amount of emails each.
        elif mt_mode == 'lim':
            n_threads = self['multithreading'][1]
            n_emails_per_thread = self['amount'] // n_threads

        # no multithreading.  1 thread, all the emails.
        elif mt_mode == 'none':
            n_threads = 1
            n_emails_per_thread = self['amount']

        # now, generate the fake options and feed them down to the worker
        # threads
        fake_options = copy.deepcopy(self._options)
        fake_options['amount'] = n_emails_per_thread

        for i in range(n_threads):
            thread = EmailSender(self, **fake_options)
            thread.name = "{} / {} / {}".format(str(i),
                                                str(n_threads),
                                                str(n_emails_per_thread))

            self._threads.append(thread)

        # double check here that we're sending the correct number
        # of emails per issue #3.
        if (mt_mode == "lim") and \
           (n_threads * n_emails_per_thread != self['amount']):
            n_leftover = self['amount'] - (n_threads * n_emails_per_thread)
            ffake_options = copy.deepcopy(self._options)
            ffake_options['amount'] = n_leftover
            thread = EmailSender(self, **ffake_options)
            thread.name = "{} / {} / {}".format(str(i + 1),
                                                str(n_threads),
                                                str(n_leftover))
            self._threads.append(thread)

        if CONFIG['debug']:
            print("EmailSendHandler generated {} threads "
                  "sending {} each".format(
                      str(n_threads), str(n_emails_per_thread)))

    def run(self):

        self.generate_send_threads()
        self._final_check()
        self.start_threads()

        # continously monitor for all threads to be done, then mark
        # self as done

        while not self.is_done:

            for thread in self._threads:
                if thread.is_done:
                    thread.join()
                    self._threads.remove(thread)

            if not self._threads:
                self.is_done = True

    def start_threads(self):
        '''Just do it!'''

        # straightforward.  go through the list self._threads and .start()
        # them all.

        for thread in self._threads:
            thread.start()

    def abort(self):
        '''Attempt to halt the sending of more emails.'''
        # Oh, fuck.  This is gonna be tough.

        self.do_abort = True

        for thread in self._threads:
            thread.do_abort = True

        # force the abort button into reset mode by faking being done sending
        # (which, we are, but not because all emails have been sent)
        self.is_done = True
        self.n_sent -= 1
        self.sent_another_one()

        # I guess that'll have to do... not like we can suddenly switch the
        # system over to an airgapped network.  I can dream.

    def sent_another_one(self):
        '''Call this exactly once per email sent.
           For updating progress bar.'''
        self.n_sent += 1

        if self._handler is not None:
            self._handler.progress_bar["value"] = self.n_sent
            self._handler.progress_label.config(text="Sent: {} / {}".format(
                str(self.n_sent), str(self["amount"])))

        # if we're done, and have a handler...
        # change abort button to reset and switch the handler functions
        if self.n_sent >= self["amount"] or self.is_done:
            self.is_done = True

            if self._handler is not None:
                self._handler.button_abort["text"] = "Reset"

                messagebox.showinfo(CONFIG['title'], "Sending complete!")


class EmailSender(threading.Thread):
    '''Class to do the dirty work of sending emails.'''

    def __init__(self, handler, **kwargs):
        self._handler = handler

        self._options = kwargs

        self.do_abort = False
        self.is_done = False

        self.n_sent = 0

        super(EmailSender, self).__init__()

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

    def build_message(self):
        '''Construct the MIME multipart message.'''
        msg = MIMEMultipart()

        # forge return headers if requested
        # use this weird and logic here to determine, in 1 swoop and error-free
        # if we have a GUI handler and if so, whether the checkbox is checked.
        # this will work because python breaks out of and gates early if the
        # first condition is false.  therefore, if there is no GUI handler,
        # the first argument is false, and the second test (forge-from) will
        # never throw an AttributeError
        if self._handler._handler and \
           (self._handler._handler.forge_from.get() == 1):
            sender = self['display_from']
        else:
            sender = self['From']

        msg.add_header('reply-to', sender)
        msg['From'] = "\"" + sender + "\" <" + \
                      sender + ">"
        msg.add_header('X-Google-Original-From',
                       '"{df}" <{df}>'.format(df=sender))

        # multiple recipients
        if isinstance(self['to'], list):
            msg['To'] = COMMASPACE.join(self['to'])
        else:
            msg['To'] = self['to']
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = self['subject']

        # if debugging, append some useful info to the bottom of the emails
        if CONFIG['debug']:

            i, n_threads, n_mails = (int(p) for p in self.name.split(" / "))

            part2 = "\n\nThread #{} of {}, sending {}/thread".format(
                str(i + 1), str(n_threads), str(n_mails))

            msg.attach(MIMEText(self['message'] + part2))
        else:
            # no debug message -- just attach the message
            msg.attach(MIMEText(self['message']))

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

    def _launch(self, nsend, _recur=0, delay=0):
        '''Send `nsend` emails.'''

        CONFIG['con_per'] = self['multithreading'][2]

        def connect():
            '''Connect to the server.  Function-ized to save typing.'''

            server = smtplib.SMTP(self['server'])
            server.ehlo_or_helo_if_needed()

            if server.has_extn("STARTTLS"):
                server.starttls()
                server.ehlo()

            # by default, mercury doesn't use AUTH!
            if server.has_extn("AUTH"):
                server.login(self['From'], self['password'])

            if CONFIG['debug']:
                server.set_debuglevel(1)

            return server

        server = connect()

        # try to send the emails.
        # in the case of a 421 error, assume temp. issue and try again with the
        # rest of the emails to be sent.
        try:
            mime = self['MIMEMessage'].as_string()
            for _ in BEST_RANGE(nsend):

                # important! check for a thread exit flag and abort if needed
                if self.do_abort:
                    raise EmergencyStop("Aborting!")
                    # hackish way to jump straight to the finally clause
                    # that closes the connection and exits.

                if CONFIG['debug']:
                    print('Launching {} at ' .format(_) + str(time.time()))

                if CONFIG['con_per']:
                    server.quit()
                    server = connect()

                server.sendmail(self['From'], self['to'],
                                mime.format(num=_ + 1))
                self._handler.sent_another_one()
                time.sleep(int(delay))

        except smtplib.SMTPServerDisconnected:
            # first, stop trying to connect to a dead server
            server.quit()
            # could happen if the internet goes out temporarily.  we just
            # try to resend and pray for the best
            sys.stderr.write('=== Server disconnected.  Trying again. ===')
            # use _recur to prevent recursion errors if the internet is out
            if _recur <= CONFIG['max_retries']:
                # send however many emails are left over
                self._launch(nsend - _, _recur=_recur + 1)
            else:
                # tried too many times, give up and make it the user's
                # problem
                raise

        except EmergencyStop:
            # if we're connecting per email, then there will be no active
            # connection to close and as such we don't need to do anything
            if CONFIG['con_per']:
                pass
            else:
                server.quit()
            return

        finally:
            # everything died.  just give up.
            server.quit()

    def run(self):
        self.build_message()

        if CONFIG['debug']:
            mime_msg = self['MIMEMessage'].as_string()
            print("Launching {} copies of message:\n{}".format(self['amount'],
                                                               mime_msg))

        self._launch(self['amount'], delay=self['delay'])

        self.is_done = True


# %% classes for user interface
class EmailPrompt(object):
    '''Prompt the user for information for emails, and send it.  Done via
    stdin/stdout.'''

    def __init__(self, _autorun=True):
        '''Make Stuff Happen'''
        self.server = self.amount = self.frm = self.delay = None
        self.multithreading = self.subject = self.files = self.text = None
        self._sender = self.rcpt = self.password = self.display_from = None

        self._all_senders = []

        if _autorun:
            self._run()

    def _make_sender(self, i=0, bar_update_handle=None):
        '''Create the EmailSender object for this email.'''
        self._sender = EmailSendHandler(bar_update_handle,
                                        server=self.server[i],
                                        From=self.frm[i],
                                        to=self.rcpt,
                                        message=self.text,
                                        subject=self.subject,
                                        multithreading=self.multithreading,
                                        attach=self.files,
                                        password=self.password[i],
                                        amount=self.amount,
                                        delay=self.delay,
                                        display_from=self.display_from)
        self._all_senders.append(self._sender)

    def send_msg(self, bar_update_handle=None):
        '''FIRE THE CANNONS!'''
        if CONFIG['debug']:
            print('Sending msg: \n{}\nfrom {} {} times'.format(self.text,
                                                               self.server,
                                                               self.amount))
        for i in BEST_RANGE(len(self.frm)):
            self._make_sender(i, bar_update_handle)
            self._sender.start()

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

    colors = {"background": CONFIG['colors']['bg'],
              }
    buttons = {"background": CONFIG['colors']['buttons'],
               "activebackground": CONFIG['colors']['bg'],
               }

    def __init__(self):
        '''Start the class, and make stuff happen.'''
        EmailPrompt.__init__(self, _autorun=False)
        self.root = tk.Tk()
        self.init_gui()

        self.root.protocol('WM_DELETE_WINDOW', self.exit)

        # self.root.mainloop needs to be called sometimes - but not always?
        # can't figure out a pattern here.
        if platform.system() in ['Linux', 'Darwin']:
            self.root.mainloop()
        if sys.version_info.major == 3 and platform.system() == 'Windows':
            self.root.mainloop()

    def exit(self):
        '''Close the window. '''
        self.root.destroy()

    def handler_button_send(self):
        '''Handle the 'Send' button being clicked.
           Tries to send the message, but if it doesn't work spawns a
           popup saying why.'''

        # ask for confirmation
        if messagebox.askyesno(CONFIG['title'],
                               ' '.join(CONFIG['confirmation_msg'])):
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
                self.send_msg(self)
            except smtplib.SMTPResponseException as exc:
                if isinstance(exc, tuple(POPUP_ERRORS)):
                    messagebox.showerror(CONFIG['title'], exc.smtp_error)
            except smtplib.SMTPException as exc:
                if isinstance(exc, tuple(POPUP_ERRORS)):
                    messagebox.showerror(CONFIG['title'], exc.args[0])

    def handler_button_abort(self):
        '''Do our best job at stopping the sending of further emails.'''

        # reset mode
        if self._sender.is_done:
            self.progress_bar["value"] = 0
            self.progress_label.config(text="Sent: 0 / 0")

            self._all_senders = []
            self._sender = None

            # switch back to abort
            self.button_abort["text"] = "Abort"

        # abort mode
        else:
            for sender in self._all_senders:
                sender.abort()

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
        self.display_from = self.entry_df.get()
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

        # Pylint yells about this.
        # It doesn't like that we redefine CONFIG['max_retries'] inside
        # something, and it doesn't see it being used in this method.
        # It is right about both, so I didn't silence it, BUT:
        # Yeah, redefining names is bad but the value isn't changed by the
        # program, only the user.
        # It's not used in this method, but is used later in the program
        # and its value can make a difference in execution.
        CONFIG['max_retries'] = int(self.entry_retry.get())
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
        # that we populate the rest of the lists with clones of the last
        # element
        if len(self.server) < len(self.frm):
            self.server += [self.server[-1]] * (len(self.frm) -
                                                len(self.server))
        if len(self.password) < len(self.frm):
            self.password += [self.password[-1]] * (len(self.frm) -
                                                    len(self.password))

    def _make_sender(self, i=0, bar_update_handler=None):
        self.create_msg_config()
        EmailPrompt._make_sender(self, i, bar_update_handler)

    def check_retcode(self):
        '''Look up an SMTP return error code and get its message.'''
        def lookup_code():
            '''Do the dirty work of setting the message to what it should
            be.'''
            retcode = int(entry_resp.get())
            if retcode not in CONFIG['SMTP_resp_codes']:
                msg = "Sorry, I don't know that one!" + (" " * (MAX_RESP_LEN -
                                                                29))
            else:
                msg = CONFIG['SMTP_resp_codes'][retcode]
                msg += (" " * (MAX_RESP_LEN - len(msg)))
            label_code.config(text=msg)

        retmen = tk.Toplevel(self.root)
        retmen.wm_title("Response codes")
        retmen.config(**self.colors)
        label_resp = tk.Label(retmen, text="Response code: ", **self.colors)
        label_resp.grid(row=0, column=0, sticky=tk.W)
        entry_resp = tk.Entry(retmen, width=4)
        entry_resp.grid(row=0, column=1, sticky=tk.W)
        label_err = tk.Label(retmen, text="Error: ", **self.colors)
        label_err.grid(row=1, column=0, sticky=tk.W)
        label_code = tk.Label(retmen, text=(' ' * 62), **self.colors)
        label_code.grid(row=1, column=1, sticky=tk.W)
        button_lookup = tk.Button(retmen, text='Look up', command=lookup_code,
                                  **self.buttons)
        button_lookup.grid(row=3, column=0, sticky=tk.W)

    def handler_button_help(self):
        """Display program documentation."""
        helper = tk.Toplevel(self.root)
        helper.title("Help")
        txt = scrolledtext.ScrolledText(helper)
        txt.insert(tk.END, GUI_DOC)
        txt['font'] = ('liberation mono', '10')
        txt.pack(expand=True, fill='both')

    def verify_to(self):
        """Verify the email address the user wants to send to and show
        a message box containing the result.  Graphical mode only."""
        def VRFY():
            '''Button handler for verify mode using SMTP VRFY verb.'''
            serv = self.entry_server.get() or CONFIG['server']
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
            serv = self.entry_server.get() or CONFIG['server']
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
        vrfymen.config(**self.colors)
        vrfymen.wm_title("Verification")
        label_from = tk.Label(vrfymen, text='Verify from:', **self.colors)
        label_from.grid(row=0, column=0, sticky=tk.W)
        entry_from = tk.Entry(vrfymen, width=40)
        entry_from.grid(row=0, column=1, columnspan=2, sticky=tk.W)
        entry_from.insert(0, self.entry_from.get().split(',')[0])
        label_password = tk.Label(vrfymen, text='Verify password:',
                                  **self.colors)
        label_password.grid(row=1, column=0, sticky=tk.W)
        entry_password = tk.Entry(vrfymen, width=40, show='*')
        entry_password.grid(row=1, column=1, columnspan=2, sticky=tk.W)
        entry_password.insert(0, self.entry_password.get())
        label_to = tk.Label(vrfymen, text='To:', **self.colors)
        label_to.grid(row=2, column=0, sticky=tk.W)
        entry_to = tk.Entry(vrfymen, width=40)
        entry_to.grid(row=2, column=1, columnspan=2, sticky=tk.W)
        entry_to.insert(0, self.entry_to.get())
        label_serv = tk.Label(vrfymen, text="Server:", **self.colors)
        label_serv.grid(row=3, column=0, sticky=tk.W)
        entry_serv = tk.Entry(vrfymen, width=40)
        entry_serv.grid(row=3, column=1, columnspan=2, sticky=tk.W)
        entry_serv.insert(0, self.entry_server.get())
        button_VRFY = tk.Button(vrfymen, text="VRFY", command=VRFY,
                                **self.buttons)
        button_VRFY.grid(row=4, column=0, sticky=tk.W)
        label_VRFY_res = tk.Label(vrfymen, text="", **self.colors)
        label_VRFY_res.grid(row=4, column=1, sticky=tk.W)
        button_MAIL = tk.Button(vrfymen, text="MAIL", command=MAIL,
                                **self.buttons)
        button_MAIL.grid(row=5, column=0, sticky=tk.W)
        label_MAIL_res = tk.Label(vrfymen, text="", **self.colors)
        label_MAIL_res.grid(row=5, column=1, sticky=tk.W)
        button_paste_addr = tk.Button(vrfymen, text="Paste address",
                                      command=paste_addr,
                                      **self.buttons)
        button_paste_addr.grid(row=6, column=0, sticky=tk.W)
        button_paste_serv = tk.Button(vrfymen, text="Paste server",
                                      command=paste_serv,
                                      **self.buttons)
        button_paste_serv.grid(row=6, column=1, sticky=tk.W)

    def init_gui(self):
        '''Build that ugly GUI.'''
        # ws = int(self.root.winfo_screenwidth() / 2)
        # hs = int(self.root.winfo_screenheight() / 2)
        self.root.title(CONFIG['title'])
        self.root.config(background=CONFIG['colors']['bg'])

        # if the length of CONFIG['text'] is greather than 100, use 100 as the
        # limit of the window width.  prevents window being wider than the
        # screen on smaller screens (laptops)
        width = CONFIG["width"]

        # number to send
        self.label_amount = tk.Label(self.root, text='# emails: ',
                                     **self.colors)
        self.label_amount.grid(row=1, column=0, sticky=tk.W)
        self.entry_amount = tk.Entry(self.root, width=5)
        self.entry_amount.grid(row=1, column=1, sticky=tk.W)
        self.entry_amount.insert(0, CONFIG['amount'])

        # subject
        self.label_subject = tk.Label(self.root, text='Subject: ',
                                      **self.colors)
        self.label_subject.grid(row=2, column=0, sticky=tk.W)
        self.entry_subject = tk.Entry(self.root, width=width)
        self.entry_subject.grid(row=2, column=1, columnspan=9,
                                sticky=tk.W + tk.E)
        self.entry_subject.insert(0, CONFIG['subject'])

        # text
        self.label_text = tk.Label(self.root, text='Message text: ',
                                   **self.colors)
        self.label_text.grid(row=7, column=0, sticky=tk.W)
        self.entry_text = tk.Entry(self.root, width=width)
        self.entry_text.grid(row=7, column=1, columnspan=9, sticky=tk.W + tk.E)
        self.entry_text.insert(0, CONFIG['text'])

        # from
        self.label_from = tk.Label(self.root, text='From | display as: ',
                                   **self.colors)
        self.label_from.grid(row=3, column=0, sticky=tk.W)
        self.entry_from = tk.Entry(self.root, width=int(width/3 * 2))
        self.entry_from.grid(row=3, column=1, columnspan=6, sticky=tk.W + tk.E)
        self.entry_from.insert(0, CONFIG['from'])

        # display from
        self.entry_df = tk.Entry(self.root, width=int(width/3))
        self.entry_df.grid(row=3, column=7, columnspan=3, sticky=tk.W + tk.E)
        self.entry_df.insert(0, CONFIG['display_from'])

        # from password
        self.label_password = tk.Label(self.root, text='Password: ',
                                       **self.colors)
        self.label_password.grid(row=4, column=0, sticky=tk.W)
        self.entry_password = tk.Entry(self.root, show='*',
                                       width=width)
        self.entry_password.grid(row=4, column=1, columnspan=9,
                                 sticky=tk.W + tk.E)
        # only allow default passwords if the user specified one
        # otherwise set it to none
        self.entry_password.insert(0, args.PASSWORD or '')

        # to
        self.label_to = tk.Label(self.root, text='To: ',
                                 **self.colors)
        self.label_to.grid(row=5, column=0, sticky=tk.W)
        self.entry_to = tk.Entry(self.root, width=width)
        self.entry_to.grid(row=5, column=2, columnspan=8)
        self.entry_to.insert(0, CONFIG['to'])

        # check email
        self.button_vrfy = tk.Button(self.root, text='Verify',
                                     command=self.verify_to,
                                     **self.buttons)
        self.button_vrfy.grid(row=5, column=1)

        # server
        self.label_server = tk.Label(self.root, text='Server: ',
                                     **self.colors)
        self.label_server.grid(row=6, column=0, sticky=tk.W)
        self.entry_server = tk.Entry(self.root, width=width)
        self.entry_server.grid(row=6, column=1, columnspan=9,
                               sticky=tk.W + tk.E)
        self.entry_server.insert(0, CONFIG['server'])

        # progress bar!
        self.progress_label = tk.Label(self.root, text="Sent: 0 / 0 ",
                                       **self.colors)
        self.progress_label.grid(row=9, column=0, sticky=tk.W)
        self.progress_bar = ttk.Progressbar(self.root, orient='horizontal',
                                            length=600, mode='determinate')
        self.progress_bar.grid(row=9, column=2, columnspan=8)

        # abort button
        self.button_abort = tk.Button(self.root, text="Abort",
                                      command=self.handler_button_abort,
                                      **self.buttons)
        self.button_abort.grid(row=9, column=1, sticky=tk.W)

        # multithreading
        self.multithread_label = tk.Label(self.root,
                                          text='Multithreading mode:',
                                          **self.colors)
        self.multithread_label.grid(row=10, column=0, sticky=tk.W)
        self.query_multithreading = tk.StringVar()
        self.query_multithreading.set(CONFIG['multithread'][0])
        self.mt_none = tk.Radiobutton(self.root, text='None',
                                      variable=self.query_multithreading,
                                      value='none',
                                      **self.colors)
        self.mt_lim = tk.Radiobutton(self.root, text='Limited: ',
                                     variable=self.query_multithreading,
                                     value='lim',
                                     **self.colors)
        self.mt_ulim = tk.Radiobutton(self.root, text='Unlimited',
                                      variable=self.query_multithreading,
                                      value='ulim',
                                      **self.colors)
        self.mt_none.grid(row=11, column=0, sticky=tk.W)
        self.mt_lim.grid(row=12, column=0, sticky=tk.W)
        self.mt_ulim.grid(row=13, column=0, sticky=tk.W)
        self.n_threads = tk.Entry(self.root, width=3)
        self.n_threads.insert(0, CONFIG['multithread'][1])
        self.n_threads.grid(row=12, column=1, sticky=tk.W)

        self.entry_delay = tk.Entry(self.root, width=3)
        self.entry_delay.grid(row=11, column=1, sticky=tk.W)
        self.entry_delay.insert(0, CONFIG['delay'])

        # file attachments
        self.file_label = tk.Label(self.root, text='Attachments: ',
                                   **self.colors)
        self.file_label.grid(row=8, column=0, sticky=tk.W)
        self.file_entry = tk.Entry(self.root, width=width)
        self.file_entry.grid(row=8, column=2, columnspan=8)
        self.file_entry.insert(0, CONFIG['attach'])
        # server options label
        self.opt_label1 = tk.Label(self.root, text='Server options:',
                                   **self.colors)
        self.opt_label1.grid(row=10, column=2, sticky=tk.W)

        # max server retry attempts
        self.label_retry = tk.Label(self.root, text='Max. Retries: ',
                                    **self.colors)
        self.label_retry.grid(row=11, column=2, sticky=tk.W)
        self.entry_retry = tk.Entry(self.root, width=3)
        self.entry_retry.insert(0, str(CONFIG['max_retries']))
        self.entry_retry.grid(row=11, column=3, sticky=tk.W)

        # connect once or per email
        self.query_conmode = tk.BooleanVar()
        self.query_conmode.set(False)
        self.con_once = tk.Radiobutton(self.root, text='Connect once',
                                       variable=self.query_conmode,
                                       value=False,
                                       **self.colors)
        self.con_per = tk.Radiobutton(self.root, text='Connect per send',
                                      variable=self.query_conmode,
                                      value=True,
                                      **self.colors)
        self.con_once.grid(row=12, column=2, sticky=tk.W)
        self.con_per.grid(row=13, column=2, sticky=tk.W)

        # compliance options
        self.label_compliance = tk.Label(self.root, text="RFC2822 Compliance",
                                         **self.colors)
        self.label_compliance.grid(row=10, column=4, sticky=tk.W)

        self.forge_from = tk.IntVar()
        self.forge_from.set(1)
        self.forge_from_box = tk.Checkbutton(self.root, text="Forge sender",
                                             variable=self.forge_from,
                                             **self.colors)
        self.forge_from_box.grid(row=11, column=4, sticky=tk.W)

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
                                           command=browse_file,
                                           **self.buttons)
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
        self.menu_clientside.add_command(label='Exit', command=self.exit)
        self.menu_top.add_cascade(label='Client', menu=self.menu_clientside)

        self.menu_help = tk.Menu(self.menu_top, tearoff=0)
        self.menu_help.add_command(label='Documentation',
                                   command=self.handler_button_help)
        self.menu_help.add_command(label='SMTP Response code lookup',
                                   command=self.check_retcode)
        self.menu_top.add_cascade(label='Help', menu=self.menu_help)

        self.root.config(menu=self.menu_top)

        # label CONFIG['debug'] mode if it is on
        if CONFIG['debug']:
            label_DEBUG = tk.Label(self.root, text='DEBUG MODE ACTIVE')
            label_DEBUG.grid(row=1, column=2)


# %% main
if __name__ == '__main__':
    try:
        sys.stdout = FakeSTDOUT(sys.stdout, CONFIG['log_stdout'])
        sys.stderr = FakeSTDOUT(sys.stderr, CONFIG['log_stderr'])
        # DO STUFF!
        if not args.NOGUI:
            EmailerGUI()
        elif args.NOGUI:
            EmailPrompt()
        elif args.COMMANDLINE:
            p = EmailPrompt(_autorun=False)
            p.send_msg()
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout = sys.stdout.FSO_close()
        sys.stderr = sys.stderr.FSO_close()