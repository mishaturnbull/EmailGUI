# -*- coding: utf-8 -*-
"""
Basic command-line user interface for the sender.
"""

from prereqs import CONFIG, BEST_RANGE, BEST_INPUT
from helpers import suggest_thread_amt
from sender import EmailSendHandler


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
