# -*- coding: utf-8 -*-
"""
Contains the Coordinator class that is responsible for communications between
all different modules of the program.
"""

import copy
import sys
import os

from emailbuilder import Email
from headers import Headers
from sender import EmailSendHandler
from gui import EmailGUI

from prereqs import CONFIG, FakeSTDOUT, CATCH_EXC
from gui_callbacks import CALLBACKS, handle_error


class Coordinator(object):
    """
    Primarily responsible for coordinating communications between all different
    classes in the program.
    """

    def __init__(self):
        """Instantiate the Coordinator object.  Automatically creates & links
        the required modules."""

        if CONFIG['settings']['debug']:
            print("coordinator.__init__: starting instantiation")

        self.settings = copy.deepcopy(CONFIG['settings'])
        self.contents = copy.deepcopy(CONFIG['contents'])
        self.callbacks = {}
        self.register_callbacks()

        self.headers = Headers(self, None)
        self.email = Email(self, self.headers)
        self.headers.email = self.email
        self.sender = EmailSendHandler(self)
        self.gui = EmailGUI(self)

        self.headers.auto_make_basics()
        self.last_exc = None

        self.ready_to_send = True

        if self.settings['debug']:
            print("coordinator.__init__: instantiation complete")

    def register_callbacks(self):
        """Given a name and a function, register the callback function."""
        # we have to convert the callback to take this as an argument...

        for cb in CALLBACKS:
            cbname = cb.__name__.split('_')[1]

            def wrapit(cbfunc):
                def wrapped():
                    try:
                        return cbfunc(self)
                    except (CATCH_EXC) as exc:
                        self.last_exc = exc
                        handle_error(self)
                return wrapped

            if self.settings['debug']:
                print("coordinator.register_callbacks: registering " + cbname)

            self.callbacks.update({cbname: wrapit(cb)})

    def retrieve_data_from_uis(self):
        """Get all the data from various UI elements."""

        if self.settings['debug']:
            print("coordinator.retrieve_data_from_uis: pulling data")

        self.gui.dump_values_to_coordinator()
    
    def prepare_to_send(self):
        """Take all the necessary actions to prepare for sending."""
        if not self.ready_to_send:
            raise RuntimeError("Currently not ready to send!")
        
        self.retrieve_data_from_uis()
        self.email.pull_data_from_coordinator()

    def send(self):
        """Send emails as configured."""
        self.sender.start()

        self.ready_to_send = False

    def callback_sent(self):
        """Action to take when an email has been sent."""
        if self.settings['debug']:
            print("coordinator recieved notification of email sent")
        self.gui.callback_sent()
        if self.settings['debug']:
            print("coordinator notification actions completed")

    def reset_sender(self):
        """Discard old sender and generate a new one."""
        self.sender.pre_delete_actions()
        self.sender = EmailSendHandler(self)
        self.retrieve_data_from_uis()

    def main(self):
        """Do stuff!"""

        for log in [self.settings['log_stdout'], self.settings['log_stderr']]:
            if os.path.exists(log):
                os.remove(log)

        sys.stdout = FakeSTDOUT(sys.stdout, self.settings['log_stdout'],
                                realtime=self.settings['realtime'])
        sys.stderr = FakeSTDOUT(sys.stderr, self.settings['log_stderr'],
                                realtime=self.settings['realtime'])

        try:
            self.gui.spawn_gui()
            self.gui.run()
        except (CATCH_EXC) as exc:
            self.last_exc = exc
            handle_error()

        sys.stdout = sys.stdout.FSO_close()
        sys.stderr = sys.stderr.FSO_close()


if __name__ == '__main__':
    C = Coordinator()
    C.main()
