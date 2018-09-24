# -*- coding: utf-8 -*-
"""
This contains the Headers class which is primarily responsible for keeping
track of the headers for an Email message.
"""

from email.utils import COMMASPACE, formatdate
import time

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
        self.add_header('sender', self.coordinator.contents['from'])
        self.add_header('to', COMMASPACE.join(
            self.coordinator.contents['to'].split(',')))
        self.add_header('from', self.coordinator.contents['from'])
