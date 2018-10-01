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

        self.headers = copy.deepcopy(self.coordinator.contents['headers'])
        self.enabled = {}

        for header in self.headers:
            self.enabled.update({header: False})
            if self.headers[header]:
                self.enabled[header] = True

    def add_header(self, header, value):
        """Add a header to the records."""

        self.headers.update({header: value})

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
        self.add_header('sender', self.coordinator.contents['account'])
        self.add_header('from', self.coordinator.contents['from'])

    def pull_from_header_gui(self, header_gui):
        """Get all the headers from the GUI."""
        for variable in header_gui.variables:
            if variable.startswith('enable_'):
                self.enabled[variable] = bool(
                    header_gui.variables[variable].get())
                continue

            if header_gui.variables['enable_' + variable].get() == 1:
                self.headers[variable] = header_gui.variables[variable].get()
            else:
                self.headers[variable] = ''

    def dump_headers_to_email(self):
        """Send all the header information to the Email class."""
        for header in self.headers:
            if self.enabled[header]:
                self.coordinator.email.add_header(header, self.headers[header])
