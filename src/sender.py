# -*- coding: utf-8 -*-
"""
This file contains the EmailSender and EmailSendHandler classes.

Together, they work to dispatch a given number of emails using a given
number of worker threads.
"""

import threading
import smtplib
import time
import sys

from prereqs import EmergencyStop


class EmailSender(threading.Thread):
    """
    This class is responsible for sending a given amount of emails in a
    worker thread environment.
    """

    def __init__(self, handler, worker_index):
        """Instantiate the EmailSender thread object.

        :handler: Must be an EmailSendHandler object.
        :worker_index: int.  Must be increased incrementally by the
                       EmailSendHandler's thread creation method.
        """
        super(EmailSender, self).__init__()

        self.handler = handler

        self.worker_index = worker_index
        self.amount = self.handler.get_amount(self.worker_index)

        self.do_abort = self.is_done = False
        self.n_sent = 0

        self.message_text = self.handler.coordinator.email.as_string()

    def establish_connection(self):
        """Establish a connection to the server specified in
        the handler's settings dictionary.  Returns an smtplib.SMTP object."""
        server = smtplib.SMTP(self.handler.settings['server'])
        server.ehlo_or_helo_if_needed()

        if server.has_extn("starttls"):
            server.starttls()
            server.ehlo()

        if server.has_extn("auth"):
            server.login(self.handler.settings['from'],
                         self.handler.settings['password'])

        if self.handler.coordinator.settings['debug']:
            server.set_debuglevel(1)

        return server

    def send_emails(self, remaining=None, retries_left=None):
        """
        Send the requested number of emails for this worker thread.

        :remaining: Internal recursive use only.
        :retries_left: Internal recursive use only.
        """

        # preconfigure localized options for a reconnection case
        sending = remaining or self.amount
        retries_left = retries_left or self.handler.settings['max_retries']

        try:

            server = self.establish_connection()

            for i in range(sending):

                if self.do_abort:
                    raise EmergencyStop("Aborting")

                if self.handler.settings['con_mode'] == 'con_per':
                    server.quit()
                    server = self.establish_connection()

                if self.handler.coordinator.settings['debug']:
                    print("Sending {} at {}".format(str(i),
                                                    str(time.time())))

                server.sendmail(self.handler.settings['from'],
                                self.handler.settings['to'],
                                self.message_text)

                self.handler.callback_sent()

                # by using timeit, it's easy to tell that
                # this if-statement is much faster than
                # simply doing time.sleep(delay) when delay = 0.
                # difference is 0.017 to 0.43 seconds
                if self.handler.settings['delay'] != 0:
                    time.sleep(self.handler.settings['delay'])

            server.quit()

        except smtplib.SMTPServerDisconnected:
            server.quit()

            if retries_left != 0:
                print("Server disconnected.  "
                      "Trying again... {} tries left.".format(retries_left),
                      file=sys.stderr)
                self.send_emails(remaining=sending-i,
                                 retries_left=retries_left-1)
            else:
                raise
        except EmergencyStop:
            if self.handler.settings['con_mode'] != 'con_per':
                server.quit()
        finally:
            self.is_done = True

    def run(self):
        """
        Start the worker thread's operation.
        """

        if self.handler.coordinator.settings['debug']:
            print("Worker thread {} starting operation at {}".format(
                self.name, time.time()))

        self.send_emails()
