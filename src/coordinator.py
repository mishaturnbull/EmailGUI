# -*- coding: utf-8 -*-
"""
Contains the Coordinator class that is responsible for communications between
all different modules of the program.
"""

from emailbuilder import Email
from headers import Headers
from sender import EmailSendHandler
from gui import EmailGUI
from header_gui import HeaderGUI

from prereqs import CONFIG
from gui_callbacks import CALLBACKS

import copy


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
        
        if self.settings['debug']:
            print("coordinator.__init__: instantiation complete")

    def register_callbacks(self):
        """Given a name and a function, register the callback function."""
        # we have to convert the callback to take this as an argument...
        
        for cb in CALLBACKS:
            cbname = cb.__name__.split('_')[1]
            
            def wrapit(cbfunc):
                def wrapped():
                    return cbfunc(self)
                return wrapped
            
            if self.settings['debug']:
                print("coordinator.register_callbacks: registering " + cbname)
    
            self.callbacks.update({cbname: wrapit(cb)})
    
    def retrieve_data_from_uis(self):
        """Get all the data from various UI elements."""
        
        if self.settings['debug']:
            print("coordinator.retrieve_data_from_uis: pulling data")
        
        self.gui.dump_values_to_coordinator()
    
    def send(self):
        """Send emails as configured."""
        
        if self.settings['debug']:
            print("coordinator: send command recieved")
        
        self.retrieve_data_from_uis()
        self.email.pull_data_from_coordinator()
        self.sender.run()
    
    def callback_sent(self):
        """Action to take when an email has been sent."""
        self.gui.variables['progressbar'].set(
            self.gui.variables['progressbar'].get() + 1)


if __name__ == '__main__':
    C = Coordinator()
    C.gui.spawn_gui()
    C.gui.root.mainloop()
