# -*- coding: utf-8 -*-
"""
This contains the Headers class which is primarily responsible for keeping
track of the headers for an Email message.
"""

from email.utils import formatdate
import uuid
import time

REQUIRED_HEADERS = ['date',     # RFC 2822
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

        self.headers = []

        # each entry should be of the form:
        # {"name": str,
        #  "value": str,
        #  "enabled": bool}
        # the keys are quite obvious I believe...
        for key, val in self.coordinator.contents['headers'].items():
            self.add_header(key, val)

        self.auto_make_basics()

    def add_header(self, header, value, enabled=None):
        """Add a header to the records."""
        h = {"name": header,
             "value": value,
             "enabled": enabled}
        if h['value'] and (enabled is None):
            h['enabled'] = True
        elif not h['value'] and (enabled is None):
            h['enabled'] = False
        self.headers.append(h)

    def add_or_update_header(self, header, value, enabled=None):
        """If a header is not already in the records, add it.  If it is,
        update it."""
        if header in self.header_list:
            # updating an existing record
            # first, check to make sure there's only 1 existing
            # copy in the list
            list = self.header_list
            try:
                idx = list.index(header, list.index(header), len(list) - 1)
            except ValueError:
                # good, a ValueError is expected if the item cannot
                # be found
                pass
            self.headers[idx].update(name=header, value=value)
            if enabled is None:
                if self.headers[idx]['value'] is '':
                    self.headers[idx]['enabled'] = False
                else:
                    self.headers[idx]['enabled'] = True
        else:
            # adding a new record, just handoff to self.add_header
            self.add_header(header, value, enabled)

    def add_nonexisting_header(self, header, value, enabled=None):
        """If a header is already in the records, do nothing.  Else, add it."""
        if header in self.header_list:
            return
        else:
            self.add_header(header, value, enabled)

    def add_if_empty(self, header, value, enabled=None):
        """If a header exists, but is empty, update it.  Else, add it."""
        if header in self.header_list:
            idx = self.header_list.index(header)
            old = self.headers[idx]['value']
            if old is '':
                self.add_or_update_header(header, value, enabled)
        else:
            self.add_header(header, value, enabled)

    # TODO: possible to add a cache of some sort here?
    # would need to clear the cache every time self.headers gets
    # updated in any way...
    @property
    def header_list(self):
        """Get the headers contained in the headers dictionary list as a
        list."""
        headers = []
        for h in self.headers:
            headers.append(h['name'])
        return headers

    def check_for_required_headers(self):
        """Determine whether or not all the required headers are present."""
        for header in REQUIRED_HEADERS:
            if header not in self.headers_list:
                return False
        return True

    def paste_headers_into_email(self):
        """Send all the header information over to the Email object."""
        for header in self.headers:
            if header['enabled']:
                self.email.add_header(header['name'], header['value'])

    def auto_make_basics(self):
        """Create the basic tags from the Coordinator settings fields."""
        self.add_if_empty('date', formatdate(time.time()))
        self.add_if_empty("message-id", str(uuid.uuid4()))
        self.add_if_empty("sender", self.coordinator.contents['account'])
        self.add_if_empty("from", self.coordinator.contents['headers']['from'])

    def pull_from_header_gui(self, header_gui):
        """Get all the headers from the GUI."""
        for i in range(len(header_gui.variables)):
            header = header_gui.variables[i]
            header['value'] = header['value'].get()
            header['enabled'] = bool(header['enabled'].get())
            self.headers[i] = header

    def dump_headers_to_email(self):
        """Send all the header information to the Email class."""
        if self.coordinator.settings['debug']:
            print("starting header dump...")
        for header in self.headers:
            if self.coordinator.settings['debug']:
                print("  on " + repr(header) + "...")
            if header['enabled']:
                if self.coordinator.settings['debug']:
                    print('  dumping with value ' + repr(header))
                self.coordinator.email.add_header(header['name'],
                                                  header['value'])
        if self.coordinator.settings['debug']:
            print("header dump complete")
