#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
EmailGUI.py provides a simple graphical interface designed to send an email.
It allows the user to login to their email and send email to exactly one
destination, from a specific SMTP server.

To import and use:
```
from EmailGUI import EmailerGUI
EmailerGUI()
```
Or simply run this file in Python, and the program will run.
"""

from __future__ import (division, print_function, generators, absolute_import)

# Misha Turnbull
# R020160506T0850
# EmailGUI.py

# %% imports and constants

import sys

from helpers import suggest_thread_amt, verify_to, verify_to_email

if sys.version_info.major == 3:
    import tkinter as tk
    import tkinter.messagebox as messagebox
    import tkinter.filedialog as filedialog
    import tkinter.scrolledtext as scrolledtext
    from tkinter import ttk
elif sys.version_info.major == 2:
    # pylint: disable=E0401
    # pylint complains about not finding tkMessageBox etc
    #  when run using python 3, because this stuff is for python 2
    #  but this block will never be executed in py3, and therefore
    #  will never throw an error
    import Tkinter as tk
    import tkMessageBox as messagebox
    import tkFileDialog as filedialog
    import ScrolledText as scrolledtext
    import ttk


_CALLBACKS = []


def handle_verify(coordinator):
    """Spawn the verification window and handle the attempts to verify an
    address."""
    root = coordinator.gui.root
    vmen = tk.Toplevel(root)
    vmen.config(**coordinator.gui.colors)
    vmen.title("Email Verification")
    # TODO: finish verify menu
_CALLBACKS.append(handle_verify)


def handle_abort(coordinator):
    """Deal with an abort button call."""
    coordinator.sender.abort()
_CALLBACKS.append(handle_abort)


def register_handlers(coordinator):
    """Register all the handlers defined into the Coordinator's list."""
    for cb in _CALLBACKS:
        cbname = cb.__name__.split('_')[1]
        coordinator.register_callback(cbname, cb)


class EmailGUI(object):
    '''Make things easier to use, and prettier.'''


    def __init__(self, coordinator):
        '''Start the class, and make stuff happen.'''

        self.coordinator = coordinator
        register_handlers(self.coordinator)
        self.root = tk.Tk()

        self.variables = {}
        self.inputs = {}

        self.colors = {"background": self.coordinator.settings['colors']['bg'],
                       }
        self.buttons = {"background":
                            self.coordinator.settings['colors']['buttons'],
                        "activebackground":
                            self.coordinator.settings['colors']['bg'],
                        }

        self.entry_width = self.coordinator.settings['width']

    def _add_label(self, text, label_opts=None, **grids):
        """Adds a tk.Label element to the root window and grids it
        using the **args provided."""
        if label_opts is None:
            label_opts = {}
        tk.Label(self.root, text=text, **label_opts,
                 **self.colors).grid(**grids)

    def _add_entry(self, varname, width=None, entry_opts=None, **grids):
        """Adds a tk.Entry element to the root window, adds the variable
        to the variables dictionary, and grids it to the window."""
        if entry_opts is None:
            entry_opts = {}
        if width is None:
            width = self.entry_width
        if width is not None:
            entry_opts.update({'width': width})
        var = tk.StringVar()
        self.variables.update({varname: var})
        entry = tk.Entry(self.root, textvariable=var, **entry_opts)
        entry.grid(**grids)
        
        # check for any default options under the varname
        if varname in self.coordinator.contents:
            var.set(self.coordinator.contents[varname])
        if varname in self.coordinator.settings:
            var.set(self.coordinator.settings[varname])

    def _add_button(self, label, callback, btn_opts=None, **grids):
        """Adds a tk.Button element to the root window, configures it,
        and grids it to the root."""
        if btn_opts is None:
            btn_opts = {}
        btn = tk.Button(self.root, text=label, command=callback,
                        **btn_opts, **self.colors)
        btn.grid(**grids)

    def spawn_gui_elements(self):
        """Instantiate all the GUI elements.  Does not spawn the GUI."""

        # start with the window meta
        self.root.title(self.coordinator.settings['title'])
        self.root.config(background=self.colors['background'])

        # number of emails
        self._add_label("# Emails:", row=0, column=0, sticky=tk.W)
        self._add_entry('amount', width=3, row=0, column=1, sticky=tk.W)

        # to field
        self._add_label("Recipient(s):", row=1, column=0, sticky=tk.W)
        self._add_button("Verify", self.coordinator.callbacks['verify'],
                         row=1, column=1)
        self._add_entry('to', row=1, column=2, columnspan=8, sticky=tk.W)

        # from field
        self._add_label("Sender(s):", row=2, column=0, sticky=tk.W)
        self._add_entry('account', row=2, column=1, columnspan=9, sticky=tk.W)

        # password field
        self._add_label("Password(s):", row=3, column=0, sticky=tk.W)
        self._add_entry('password', entry_opts={'show': '*'},
                        row=3, column=1, columnspan=9, sticky=tk.W)

        # subject field
        self._add_label("Subject line:", row=4, column=0, sticky=tk.W)
        self._add_entry('subject', row=4, column=1, columnspan=9, sticky=tk.W)

        # text field
        self._add_label("Email message:", row=5, column=0, sticky=tk.W)
        self._add_entry('text', row=5, column=1, columnspan=9, sticky=tk.W)

        # server
        self._add_label("Server:", row=6, column=0, sticky=tk.W)
        self._add_entry('server', row=6, column=1, columnspan=9, sticky=tk.W)

        # progress bar
        # no helper function here :(
        self._add_label("Progress:", row=7, column=0, sticky=tk.W)
        self._add_button('Abort', self.coordinator.callbacks['abort'],
                         row=7, column=1)
        self.variables.update({'progressbar': tk.IntVar()})
        bar = ttk.Progressbar(self.root, orient='horizontal', length=564,
                              mode='determinate',
                              variable=self.variables['progressbar'])
        bar.grid(row=7, column=2, columnspan=8, sticky=tk.W)
