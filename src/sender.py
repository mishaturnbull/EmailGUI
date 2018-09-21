# -*- coding: utf-8 -*-
"""
Base classes, methods, worker threads and manager for multithreaded-capable
email sending.
"""

from __future__ import (division, print_function, absolute_import, generators)

import threading
import copy
import os
import time
import smtplib
import sys

from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders

from prereqs import CONFIG, EmergencyStop, BEST_RANGE, messagebox


class EmailSendHandler(threading.Thread):
    '''Handle a group of EmailSender classes.'''

    def __init__(self, bar_update_handle, **kwargs):
        super(EmailSendHandler, self).__init__()
        self._handler = bar_update_handle

        self._options = kwargs
        self._check_config()

        if self._handler is not None:
            self._handler['bar_progress']["maximum"] = self["amount"]

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
            self._handler['bar_progress']["value"] = self.n_sent
            self._handler['label_progress'].config(text="Sent: {} / {}".format(
                str(self.n_sent), str(self["amount"])))

        # if we're done, and have a handler...
        # change abort button to reset and switch the handler functions
        if self.n_sent >= self["amount"] and not self.is_done:
            self.is_done = True

            if self._handler is not None:
                self._handler['button_abort']["text"] = "Reset"

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
