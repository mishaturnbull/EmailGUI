# -*- coding: utf-8 -*-
"""
Contains the Coordinator class that is responsible for communications between
all different modules of the program.
"""

from emailbuilder import Email
from headers import Headers
from sender import EmailSendHandler
from gui import EmailGUI

from prereqs import CONFIG

import copy


class Coordinator(object):
    """
    Primarily responsible for coordinating communications between all different
    classes in the program.
    """

    def __init__(self):
        """Instantiate the Coordinator object.  Automatically creates & links
        the required modules."""

        self.settings = copy.deepcopy(CONFIG['settings'])
        self.contents = copy.deepcopy(CONFIG['contents'])
        self.callbacks = {}

        self.headers = Headers(self, None)
        self.email = Email(self, self.headers)
        self.headers.email = self.email
        self.sender = EmailSendHandler(self)
        self.gui = EmailGUI(self)

    def register_callback(self, name, callback):
        """Given a name and a function, register the callback function."""
        # we have to convert the callback to take this as an argument...

        def wrapped_callback():
            return callback(self)

        self.callbacks.update({name: wrapped_callback})


if __name__ == '__main__':
    C = Coordinator()
    C.gui.spawn_gui()
    C.gui.root.mainloop()
