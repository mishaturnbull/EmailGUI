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


class EmailSendHandler(threading.Thread):
    """
    This class is responsible for managing multiple worker threads to
    send a given number of emails.
    """

    def __init__(self, coordinator):
        """
        Instantiate the EmailSendHandler object.

        :coordinator: Must be a Coordinator object.
        """
        super(EmailSendHandler, self).__init__()

        self.coordinator = coordinator

        self.worker_amounts = []
        self.workers = []
        self.n_sent = 0

        self.is_done = self.do_abort = False

    def create_worker_configurations(self):
        """
        Creates the list of number of emails per thread for each thread using
        the specified threading settings.
        """

        if self.coordinator.settings['mt_mode'] == 'none':
            num_threads = 1
        elif self.coordinator.settings['mt_mode'] == 'limited':
            num_threads = self.coordinator.settings['mt_num']
        elif self.coordinator.settings['mt_mode'] == 'unlimited':
            num_threads = self.coordinator.settings['amount']
        else:
            assert False, "got num_threads = " + repr(num_threads)

        emails_per_thread = self.coordinator.settings['amount'] // num_threads

        # split the load evenly among all threads
        self.worker_amounts = [emails_per_thread] * num_threads

        # check that the total count still equals the requested number,
        # which can happen on, for example:
        # amount = 100
        # n_threads = 14
        # the above code will split the load into 14 threads, sending
        # 7 emails per.  7*14 = 98, which is not the desired 100.
        sending = sum(self.worker_amounts)
        if sending != self.coordinator.settings['amount']:
            # deal with this case by adding 1 to as many
            # threads as we are short emails.  In the above case,
            # this turns
            # worker_amounts = [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7]
            # into
            # worker_amounts = [8, 8, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7]
            n_increases = self.coordinator.settings['amount'] - sending
            for i in range(n_increases):
                self.worker_amounts[i] = self.worker_amounts[i] + 1

        if self.coordinator.settings['debug']:
            print("emailsendhandler.create_worker_configurations: done: " +
                  repr(self.worker_amounts))

    def get_amount(self, worker_index):
        """
        Returns how many emails a specified worker thread is required to
        send.
        """
        return self.worker_amounts[worker_index]

    def spawn_worker_threads(self):
        """
        Create the required number of worker threads.
        """
        if self.coordinator.settings['debug']:
            print("emailsendhandler.spawn_worker_threads: creating work pool")
        for i in range(len(self.worker_amounts)):
            worker = EmailSender(self, i)

            # faster to concat than format, per timeit
            worker.name = "Thread #" + str(i)

            # add to the list
            self.workers.append(worker)

    def start_workers(self):
        """Start all the worker threads sending emails."""

        if self.coordinator.settings['debug']:
            print("emailsendhandler.start_workers: "
                  "sending start command to pool")
        for worker in self.workers:
            worker.start()

    def run(self):
        """
        Start the manager thread.
        Automatically generates sending distribution, worker threads, and
        runs the workers.
        """
        self.create_worker_configurations()
        self.spawn_worker_threads()
        self.start_workers()
        
        while not self.is_done:
            for worker in self.workers:
                if worker.is_done:
                    worker.join()
                    self.workers.remove(worker)

            if not self.workers:
                self.is_done = True

    def abort(self):
        """
        Send the abort signal to all worker threads and attempt to halt
        the further sending of emails.
        """

        self.do_abort = True

        for worker in self.workers:
            worker.do_abort = True

    def callback_sent(self):
        """
        Takes action when each email is sent.  Mainly reports upwards to
        the coordinator for updating progress information.
        """

        if self.coordinator.settings['debug']:
            print("emailsendhandler received notification of a sent email")

        self.coordinator.callback_sent()

        if self.coordinator.settings['debug']:
            print("emailsendhandler pushed pbar update")

        self.n_sent += 1

        if self.n_sent == self.coordinator.settings['amount']:
            self.is_done = True

        if self.coordinator.settings['debug']:
            print("emailsendhandler notification actions complete")
    
    def pre_delete_actions(self):
        """Actions to take before being discarded."""
        if not self.is_done:
            raise RuntimeError("Cannot reset before completing!")
        for worker in self.workers:
            worker.pre_delete_actions()
        self.workers = None


# %% Atom worker thread

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

        self.is_done = False
        self.n_sent = 0

        self.message = self.handler.coordinator.email.getmime()

    def establish_connection(self, blocking=False):
        """Establish a connection to the server specified in
        the handler's settings dictionary.  Returns an smtplib.SMTP object."""

        try:
            server = smtplib.SMTP(self.handler.coordinator.settings['server'])
        except ConnectionRefusedError:
            if blocking:
                time.sleep(self.handler.coordinator.settings[
                    'wait_dur_on_retry'])
                return self.establish_connection(blocking)
            else:
                raise
        server.ehlo_or_helo_if_needed()

        if server.has_extn("starttls"):
            server.starttls()
            server.ehlo()

        if server.has_extn("auth"):
            server.login(self.handler.coordinator.settings['from'],
                         self.handler.coordinator.settings['password'])

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
        retries_left = retries_left or \
            self.handler.coordinator.settings['max_retries']

        try:

            server = self.establish_connection()

            for i in range(sending):

                if self.handler.do_abort:
                    raise EmergencyStop("Aborting")

                con_mode = self.handler.coordinator.settings['con_mode']
                con_num = self.handler.coordinator.settings['con_num']

                d_per = con_mode == 'con_per'
                d_some = (con_mode == 'con_some') and (i % con_num == 0)
                d_some = (not d_some) if i == 0 else d_some

                if d_per or d_some:
                    server.quit()
                    server = self.establish_connection()

                if self.handler.coordinator.settings['debug']:
                    print("Sending {} at {}".format(str(i),
                                                    str(time.time())))

                server.sendmail(self.message['from'],
                                self.handler.coordinator.contents['to'],
                                self.message.as_string())

                if self.handler.coordinator.settings['debug']:
                    print("Sent successfully!")

                self.handler.callback_sent()

                if self.handler.coordinator.settings['debug']:
                    print("Completed send callback")

                # by using timeit, it's easy to tell that
                # this if-statement is much faster than
                # simply doing time.sleep(delay) when delay = 0.
                # difference is 0.017 to 0.43 seconds
                delay = self.handler.coordinator.settings['delay']
                if delay != 0:
                    if self.handler.coordinator.settings['debug']:
                        print("about to sleep for " + str(delay))
                    time.sleep(delay)

            server.quit()

        except smtplib.SMTPServerDisconnected:
            try:
                server.quit()
            except smtplib.SMTPServerDisconnected:
                # already closed one way or another
                pass

            if retries_left != 0:
                print("Server disconnected.  "
                      "Trying again... {} tries left.".format(retries_left),
                      file=sys.stderr)
                self.send_emails(remaining=sending-i,
                                 retries_left=retries_left-1)
            else:
                raise
        except EmergencyStop:
            if self.handler.coordinator.settings['con_mode'] != 'con_per':
                server.quit()
        finally:
            self.is_done = True

        if self.handler.coordinator.settings['debug']:
            print("emailsender.send_emails: done and returning")

    def run(self):
        """
        Start the worker thread's operation.
        """

        if self.handler.coordinator.settings['debug']:
            print("Worker thread {} starting operation at {}".format(
                self.name, time.time()))

        self.send_emails()
        
        if self.handler.coordinator.settings['debug']:
            print("Worker thread {} ending operation at {}".format(
                self.name, time.time()))
    
    def pre_delete_actions(self):
        """Actions to take before being deleted."""
        assert self.is_done
