# -*- coding: utf-8 -*-
"""
Contains the Email class that handles generation of the email message
per configuration defined in the Coordinator class.
"""

from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

import os
from sys import getsizeof


class PayloadGenerator(object):
    """
    This class is responsible for generating random payloads of different
    types and sizes.
    """

    def __init__(self, coordinator):
        """
        Instantiate the PayloadGenerator object and link it to a Coordinator.
        """
        self.coordinator = coordinator
        self._lorem_ipsum = ''

    def _load_lorem(self):
        """Check to see if we've loaded the lorem ipsum text, and if not,
        load it."""
        if self._lorem_ipsum != '':
            return
        with open('lorem.txt', 'r') as lorem:
            lines = lorem.readlines()
        for line in lines:
            self._lorem_ipsum += line.strip()

    def get_random_text(self, bytecount):
        """Return a chunk of text with a specified byte count."""
        out = ""
        i = 0
        self._load_lorem()
        while getsizeof(out) < bytecount:
            if i >= len(self._lorem_ipsum):
                i = 0
            out += self._lorem_ipsum[i]
            i += 1
        return out


class Email(object):
    """
    This class is responsible for constructing a MIMEMultipart message
    given details defined in the Coordinator class and the Header class.

    It is able to output the final email message as a string.
    """

    def __init__(self, coordinator, headers):
        """Instantiate the Email object given the Coordinator and headers."""

        self.coordinator = coordinator
        self.headers = headers

        self.mimemulti = MIMEMultipart()

    def add_text(self, text):
        """Attach a chunk of text to the message."""
        mimetext = MIMEText(text)
        self.mimemulti.attach(mimetext)

    def add_header(self, header, value, **options):
        """Add a header to the message header section."""
        self.mimemulti.add_header(header, value, **options)

    def add_attachment(self, filename):
        """Add a file attachment."""
        # I'm absolutely sure I stole this code off stackoverflow somewhere
        # about 2 years ago, but I have absolutely no idea where.
        # Credit to StackOverflow for this method.
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(filename, 'rb').read())
        encoders.encode_base64(part)  # modifies in-place.  magic.
        filepath = os.path.basename(filename)
        part.add_header('Content-Disposition',
                        'attachment; filename="{}"'.format(filepath))
        self.mimemulti.attach(part)

    def pull_data_from_coordinator(self):
        """Pull in the data from the coordinator."""
        self.add_text(self.coordinator.contents['text'])
        for attach in self.coordinator.contents['attach'].split(','):
            if not attach:
                continue
            attach = attach.strip()
            self.add_attachment(attach)
        self.headers.dump_headers_to_email()
        # subject is technically a header in MIME...
        self.add_header('subject', self.coordinator.contents['subject'])

    def getmime(self):
        """Returns the MIMEMultipart object."""
        return self.mimemulti

    def as_string(self):
        """Returns the stored email message as a string."""
        return self.mimemulti.as_string()
