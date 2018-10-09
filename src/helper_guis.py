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
elif sys.version_info.major == 2:
    import Tkinter as tk
    import tkSimpleDialog as simpledialog


class HeaderGUI(GUIBase):
    """This class is responsible for the GUI that allows the user to
    enter/alter different email headers."""

    def __init__(self, coordinator):
        """Instantiate the header menu."""
        super(HeaderGUI, self).__init__(coordinator, coordinator.gui.root)

        self.entry_width = self.entry_width // 3

        self._max_rows = 10
        self._row = 1
        self._column = 0

        self.root.protocol("WM_DELETE_WINDOW", self.close_action)

    def _add_entry(self, varname, root=None, width=None, entry_opts=None, 
                   **grids):
        """Wrapper for GUIBase's _add_entry method.  Autofills from the
        header sub-dictionary in contents."""
        super(HeaderGUI, self)._add_entry(varname, width, entry_opts, **grids)
        self.variables[varname].set(
            self.coordinator.headers.headers[varname])

    def _add_box(self, name, label, root=None, box_opts=None, **grids):
        """Wrapper for GUIBase's _add_box method.  Auto-enables if the
        corresponding header is enabled."""
        box_opts = box_opts or {}

        self.variables.update({'enabled_' + name: tk.IntVar()})
        if self.variables[name].get() != '':
            self.variables['enabled_' + name].set(1)

        box = tk.Checkbutton(self.root, text=label,
                             variable=self.variables['enabled_' + name],
                             **box_opts, **self.colors)
        box.grid(**grids)

        return box

    def close_action(self):
        """Close the window."""
        self.dump_values_to_headers()
        self.root.destroy()

    def dump_values_to_headers(self):
        """Output the values to the header class."""
        self.coordinator.headers.pull_from_header_gui(self)

    def _spawn_field(self, header_name):
        """Add a header field in the next spot with default name & value."""
        if self._row >= self._max_rows:
            self._row = 1
            self._column += 2

        self._add_entry(header_name, row=self._row, column=(self._column + 1),
                        sticky='w')
        self._add_box(header_name, header_name + ":",
                      row=self._row, column=self._column, sticky='w')

        self._row += 1

    def _add_custom_header(self):
        """Add a custom header box."""
        header = simpledialog.askstring("Add Custom Header",
                                        "Enter the header name:",
                                        parent=self.root)
        if header is None:
            return  # user hit cancel
        self.coordinator.headers.add_header(header, "")
        self._spawn_field(header)

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
                                              coordinator.gui.root)
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

    def _add_changinglabel(self, text, varname, root=None, label_opts=None,
                           **grids):
        """Adds a label that uses a variable for its text."""
        label_opts = label_opts or {}
        root = root or self.root
        var = tk.StringVar()
        self.variables.update({varname: var})
        var.set(text)
        lbl = tk.Label(root, textvariable=var, **label_opts, **self.colors)
        lbl.grid(**grids)
        return lbl

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
