# -*- coding: utf-8 -*-
"""
This contains the Headers class which is primarily responsible for keeping
track of the headers for an Email message.
"""

from email.utils import formatdate
import time
import copy

REQUIRED_HEADERS = [
    'date',     # RFC 2822
    'sender',   # RFC 2822
    'from',     # RFC 2822
    'to',       # ensures delivery
    ]


class Headers(object):
    """This class is responsible for managing the headers of an email message.
    """

    def __init__(self, coordinator, email):
        """Instantiate the Headers object.
        """
        self.coordinator = coordinator
        self.email = email

        self.headers = {}
        self.enabled = {}
        #import pdb; pdb.set_trace()
        for header in self.coordinator.contents['headers']:
            self.add_header(header,
                            self.coordinator.contents['headers'][header])

    def add_header(self, header, value):
        """Add a header to the records."""
        self.headers.update({header: value})
        self.enabled.update({header: bool(value)})

    def update_header(self, header, value):
        """Update an existing header with a new value.
        If the header does not exist already, add it."""

        if header in self.headers:
            self.headers[header] = value
        else:
            self.headers.update({header: value})

    def check_for_required_headers(self):
        """Determine whether or not all the required headers are present."""
        for header in REQUIRED_HEADERS:
            if header not in self.headers:
                return False
        return True

    def paste_headers_into_email(self):
        """Send all the header information over to the Email object."""
        for header in self.headers:
            self.email.add_header(header, self.headers[header])

    def auto_make_basics(self):
        """Create the basic tags from the Coordinator settings fields."""
        self.add_header('date', formatdate(time.time()))
        fields = {'sender': 'account', 'from': 'from'}
        for field in fields:
            if field not in self.headers:
                self.add_header(field,
                                self.coordinator.contents[fields[field]])

    def pull_from_header_gui(self, header_gui):
        """Get all the headers from the GUI."""
        for variable in header_gui.variables:
            # if we have a control variable
            if variable.startswith('enabled_'):
                variable = variable.split('_')[1]
                self.enabled[variable] = \
                    header_gui.variables['enabled_' + variable].get() == 1
            # otherwise, we have the value of the header
            else:
                self.headers[variable] = header_gui.variables[variable].get()
                

    def dump_headers_to_email(self):
        """Send all the header information to the Email class."""
        if self.coordinator.settings['debug']:
            print("starting header dump...")
        for header in self.headers:
            if self.coordinator.settings['debug']:
                print("  on " + header + "...")
            if self.enabled[header]:
                if self.coordinator.settings['debug']:
                    print('  dumping with value ' + repr(self.headers[header]))
                self.coordinator.email.add_header(header, self.headers[header])
        if self.coordinator.settings['debug']:
            print("header dump complete")
