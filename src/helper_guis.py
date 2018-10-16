# -*- coding: utf-8 -*-
"""
Contains the header edit submenu.
"""

import sys
import re

from gui import GUIBase
from helpers import verify_to, verify_to_email, check_rfc_5322

if sys.version_info.major == 3:
    import tkinter as tk
    from tkinter import simpledialog
    from tkinter import scrolledtext
    import tkinter.ttk as ttk
elif sys.version_info.major == 2:
    import Tkinter as tk
    import tkSimpleDialog as simpledialog
    import tkScrolledText as scrolledtext
    import ttk


class HeaderGUI(GUIBase):
    """This class is responsible for the GUI that allows the user to
    enter/alter different email headers."""

    def __init__(self, coordinator):
        """Instantiate the header menu."""
        super(HeaderGUI, self).__init__(coordinator, coordinator.gui.root,
                                        name='headers')

        self.variables = []

        self.entry_width = self.entry_width // 3

        self._max_rows = 10
        self._row = 1
        self._column = 0

    def _add_entry(self, idx, root=None, width=None, entry_opts=None,
                   **grids):
        """Wrapper for GUIBase's _add_entry method.  Autofills from the
        header sub-dictionary in contents."""
        entry_opts = entry_opts or {}
        width = width or self.entry_width
        entry_opts.update(width=width)
        root = root or self.root

        self.variables[idx]['value'] = tk.StringVar()
        if self.variables[idx]['name'] in self.coordinator.headers.header_list:
            # vagrant syntax abuse, but necessary to keep this from being
            # 9000 characters long
            name = self.variables[idx]['name']
            hlidx = self.coordinator.headers.header_list.index(name)
            hlinfo = self.coordinator.headers.headers[hlidx]
            value = hlinfo['value']
            self.variables[idx]['value'].set(value)

        entry = tk.Entry(root, textvariable=self.variables[idx]['value'],
                         **entry_opts)
        entry.grid(**grids)

        return entry

    def _add_box(self, idx, label, root=None, box_opts=None, **grids):
        """Wrapper for GUIBase's _add_box method.  Auto-enables if the
        corresponding header is enabled."""
        box_opts = box_opts or {}
        root = root or self.root

        self.variables[idx]['enabled'] = tk.IntVar()
        if self.variables[idx]['value'].get() is not '':
            self.variables[idx]['enabled'].set(1)

        box = tk.Checkbutton(root, text=label,
                             variable=self.variables[idx]['enabled'],
                             **box_opts, **self.colors)
        box.grid(**grids)

        return box

    def close_action(self):
        """Close the window."""
        self.dump_values_to_headers()

    def dump_values_to_headers(self):
        """Output the values to the header class."""
        self.coordinator.headers.pull_from_header_gui(self)

    def _spawn_field(self, header_info):
        """Add a header field in the next spot with default name & value."""
        if self._row >= self._max_rows:
            self._row = 1
            self._column += 2

        self.variables.append({"name": header_info['name'],
                               "value": None,
                               "enabled": None})

        self._add_entry(-1, row=self._row, column=(self._column + 1),
                        sticky='w')
        self._add_box(-1, header_info['name'] + ":",
                      row=self._row, column=self._column, sticky='w')

        self._row += 1

    def _add_custom_header(self):
        """Add a custom header box."""
        self.root.grab_set()
        header = simpledialog.askstring("Add Custom Header",
                                        "Enter the header name:",
                                        parent=self.root)
        if header is None:
            return  # user hit cancel
        self.coordinator.headers.add_header(header, "")
        self._spawn_field(self.coordinator.headers.headers[-1])

    def spawn_gui_basics(self):
        """Spawn the base parts of the GUI."""

        self.root.wm_title("Edit Headers")
        self.root.config(**self.colors)

        self._add_button('Add Custom Header', self._add_custom_header,
                         row=0, column=int(self._column / 2), columnspan=2,
                         sticky='ew')

        for header in self.coordinator.headers.headers:
            self._spawn_field(header)


class VerificationGUI(GUIBase):
    """This class handles the graphical interface for verifying an
    email is valid and exists."""

    def __init__(self, coordinator):
        """Instantiate the VerificationGUI."""
        super(VerificationGUI, self).__init__(coordinator,
                                              coordinator.gui.root,
                                              'verification')
        self.entry_width = self.entry_width // 3

        with open("validation.regex", 'r') as regex:
            lines = regex.readlines()
        pattern = ''
        for line in lines:
            pattern += line.strip()

        self.regex = re.compile(pattern)

    def _add_entry(self, varname, root=None, width=None, entry_opts=None,
                   **grids):
        """Adds a tk.Entry element to the window, and links the variable
        to the main GUI's."""
        if entry_opts is None:
            entry_opts = {}
        if width is None:
            width = self.entry_width
        if width is not None:
            entry_opts.update({"width": width})
        if root is None:
            root = self.root

        var = self.coordinator.gui.variables[varname]
        entry = tk.Entry(root, textvariable=var, **entry_opts)
        entry.grid(**grids)

        return entry

    def verify_syntax(self):
        """Verify that the email provided is compliant with RFC5322 grammar."""
        self.variables['output_5322'].set('Please wait...')
        if check_rfc_5322(self.coordinator.gui.variables['to'].get()):
            msg = "Email is RFC5322 grammar compliant"
        else:
            msg = "Email is *not* compliant with RFC5322 grammar"

        self.variables['output_5322'].set(msg)

    def verify_using_vrfy(self):
        """Verify an email using SMTP VRFY command."""
        serv = self.coordinator.gui.variables['server'].get()
        self.variables['output_vrfy'].set('Please wait...')
        resp = verify_to(self.coordinator.gui.variables['to'].get(), serv)
        resp = resp[0]
        if resp == 250:
            msg = str(resp) + " Email appears valid."
        elif resp == 251:
            msg = str(resp) + " Email appears forwarded."
        elif resp == 252:
            msg = str(resp) + " Server could not determine."
        else:
            msg = str(resp) + " Address either invalid or " \
                              "unable to determine."
        self.variables['output_vrfy'].set(msg)

    def verify_using_mail(self):
        '''Verify an email by trying to email it.'''
        serv = self.coordinator.gui.variables['server'].get()
        self.variables['output_email'].set('Please wait...')
        resp = verify_to_email(self.coordinator.gui.variables['to'].get(),
                               serv,
                               self.coordinator.gui.variables['account'].get(),
                               self.coordinator.gui.variables[
                                   'password'].get())
        resp = resp[0]
        if resp == 550:
            msg = str(resp) + " Email appears invalid."
        elif resp == 250:
            msg = str(resp) + " Email appears valid."
        else:
            msg = str(resp) + " Could not determine."
        self.variables['output_email'].set(msg)

    def build_gui(self):
        """Create all the GUI elements."""

        self._add_label("Account: ", row=0, column=0, sticky='w')
        self._add_entry("account", row=0, column=1, sticky='ew')

        self._add_label("Password: ", row=1, column=0, sticky='w')
        self._add_entry("password", entry_opts={"show": "*"},
                        row=1, column=1, sticky='ew')

        self._add_label("Verifying: ", row=2, column=0, sticky='w')
        self._add_entry("to", row=2, column=1, sticky='ew')

        self._add_label("Server: ", row=3, column=0, sticky='w')
        self._add_entry("server", row=3, column=1, sticky='ew')

        self._add_button("RFC5322", self.verify_syntax,
                         row=4, column=0, sticky='w')
        self._add_changinglabel("", 'output_5322', row=4, column=1, sticky='w')

        self._add_button("SMTP VRFY", self.verify_using_vrfy,
                         row=5, column=0, sticky='w')
        self._add_changinglabel("", 'output_vrfy', row=5, column=1, sticky='w')

        self._add_button("Try emailing", self.verify_using_mail,
                         row=6, column=0, sticky='w')
        self._add_changinglabel("", 'output_email', row=6, column=1,
                                sticky='w')


class EmailEditorGUI(GUIBase):
    """This class is responsible for handling email editing in a blown-up
    window.  It is also capable of adding/removing payloads and attachments.
    """

    def __init__(self, coordinator):
        """Instantiate the editor GUI instance."""
        super(EmailEditorGUI, self).__init__(coordinator,
                                             coordinator.gui.root,
                                             'editor')

    def close_action(self):
        """Deregister the GUI with the coordinator."""
        self.sync_to_main()

    def sync_from_main(self):
        """Pull the data (message) from the coordinator."""
        self.editor.insert(tk.END, self.coordinator.contents['text'])

    def sync_to_main(self):
        """Push data (message) back to coordinator."""
        # 'end-1c' comes from a SO answer
        # credit to Bryan Oakley
        # https://stackoverflow.com/a/14824164/4612410
        self.coordinator.contents['text'] = self.editor.get("1.0", 'end-1c')
        self.coordinator.active_guis['main'].pull_values_from_coordinator()

    def spawn_gui_elements(self):
        """Create the GUI elements necessary."""
        leftframe = tk.LabelFrame(self.root, text="Payloads",
                                  relief=tk.RIDGE, **self.colors)
        leftframe.grid(row=0, column=0, rowspan=4, columnspan=1, sticky='w')

        rightframe = tk.Frame(self.root, **self.colors)
        rightframe.grid(row=0, column=1, rowspan=10, columnspan=10,
                        sticky='nesw')

        self.editor = scrolledtext.ScrolledText(rightframe,
                                                wrap=tk.WORD,
                                                width=60,
                                                height=20)
        self.editor.grid(row=0, column=0)

        self._add_button('Random Payload',
                         self.coordinator.callbacks['addRandomPayload'],
                         root=leftframe,
                         row=0, column=0, sticky='ew')


class SMTPResponseCodeLookupGUI(GUIBase):
    """This class is responsible for using looking up SMTP response codes
    in a user-friendly manner."""

    def __init__(self, coordinator):
        """Instantiate the resp. code lookup GUI."""
        super(SMTPResponseCodeLookupGUI, self).__init__(coordinator,
                                                        coordinator.gui.root,
                                                        "codelookup")

        self.codes = self.coordinator.overall_config['SMTP_resp_codes']

    def do_lookup(self):
        """Handle the action for looking up a response code."""
        # TODO: implement this!
        code = self.entryvar.get()
        try:
            message = self.codes[code]
        except KeyError:
            # couldn't find it
            message = "I don't know that response code!"
        self.variables['output'].set(message)

    def spawn_gui(self):
        """Create the window."""

        # TODO: redo this using self._add_combobox now that that exists
        self.entryvar = tk.StringVar()
        self.entry = ttk.Combobox(self.root, textvariable=self.entryvar,
                                  height=len(self.codes), width=8)
        self.entry.grid(row=0, column=0, sticky='w')

        self.entry['values'] = list(self.codes.keys())

        self._add_button("Lookup", callback=self.do_lookup, row=0, column=1,
                         sticky='w')

        self._add_changinglabel(text=" "*60, varname="output", row=0,
                                column=2, sticky='w')
