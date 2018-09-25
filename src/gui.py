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


class EmailGUI(object):
    '''Make things easier to use, and prettier.'''


    def __init__(self, coordinator):
        '''Start the class, and make stuff happen.'''

        self.coordinator = coordinator
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

    def spawn_gui(self):
        """Spawn the entire GUI."""
        self.spawn_gui_basics()
        self.spawn_gui_settings()
        self.spawn_gui_menubar()

    def spawn_gui_basics(self):
        """Instantiate all the GUI elements.  Does not spawn the GUI."""

        # start with the window meta
        self.root.title(self.coordinator.settings['title'])
        self.root.config(background=self.colors['background'])

        # number of emails
        self._add_label("# Emails:", row=0, column=0, sticky=tk.W)
        self._add_entry('amount', width=3, row=0, column=1, sticky=tk.W+tk.E)

        # to field
        self._add_label("Recipient(s):", row=1, column=0, sticky=tk.W)
        self._add_button("Verify", self.coordinator.callbacks['verify'],
                         row=1, column=1)
        self._add_entry('to', row=1, column=2, columnspan=8,
                        sticky=tk.W+tk.E)

        # from field
        self._add_label("Sender(s):", row=2, column=0, sticky=tk.W)
        self._add_entry('account', row=2, column=1, columnspan=9,
                        sticky=tk.W+tk.E)

        # password field
        self._add_label("Password(s):", row=3, column=0, sticky=tk.W)
        self._add_entry('password', entry_opts={'show': '*'},
                        row=3, column=1, columnspan=9, sticky=tk.W+tk.E)

        # subject field
        self._add_label("Subject line:", row=4, column=0, sticky=tk.W)
        self._add_entry('subject', row=4, column=1, columnspan=9,
                        sticky=tk.W+tk.E)

        # text field
        self._add_label("Email message:", row=5, column=0, sticky=tk.W)
        self._add_entry('text', row=5, column=1, columnspan=9,
                        sticky=tk.W+tk.E)

        # server
        self._add_label("Server:", row=6, column=0, sticky=tk.W)
        self._add_entry('server', row=6, column=1, columnspan=9,
                        sticky=tk.W+tk.E)

        # attachments
        self._add_label("Attachments:", row=7, column=0, sticky=tk.W)
        self._add_button("Browse", self.coordinator.callbacks['browse'],
                         row=7, column=1)
        self._add_entry('attachments', row=7, column=2, columnspan=8,
                        sticky=tk.W+tk.E)

        # progress bar
        # no helper function here :(
        self._add_label("Progress:", row=8, column=0, sticky=tk.W)
        self._add_button('Abort', self.coordinator.callbacks['abort'],
                         row=8, column=1)
        self.variables.update({'progressbar': tk.IntVar()})
        # pylint: disable=C0102
        # "Blacklisted name 'bar'"
        # In this case, 'bar' makes perfect sense and is not
        # being used as in foo/bar/baz
        bar = ttk.Progressbar(self.root, orient='horizontal', length=564,
                              mode='determinate',
                              variable=self.variables['progressbar'])
        bar.grid(row=8, column=2, columnspan=8, sticky=tk.W)

    def spawn_gui_settings(self):
        """Spawn the lower-section GUI settings for multithreading, etc."""

        self.variables.update({"mt_mode": tk.StringVar()})
        self.variables['mt_mode'].set(self.coordinator.settings['mt_mode'])

        self._add_label("Multithreading options:", row=9, column=0,
                        columnspan=2)
        rb_none = tk.Radiobutton(self.root, text="None",
                                 variable=self.variables['mt_mode'],
                                 value="none",
                                 **self.colors)
        rb_none.grid(row=10, column=0, sticky=tk.W)

        rb_lim = tk.Radiobutton(self.root, text="Limited",
                                variable=self.variables['mt_mode'],
                                value='limited',
                                **self.colors)
        rb_lim.grid(row=11, column=0, sticky=tk.W)

        rb_ulim = tk.Radiobutton(self.root, text="Unlimited",
                                 variable=self.variables['mt_mode'],
                                 value="unlimited",
                                 **self.colors)
        rb_ulim.grid(row=12, column=0, sticky=tk.W)

        self._add_entry('delay', width=4, row=10, column=1, sticky=tk.W)
        self._add_entry('mt_num', width=4, row=11, column=1, sticky=tk.W)

        self.variables.update({'con_mode': tk.StringVar()})
        self.variables['con_mode'].set(self.coordinator.settings['con_mode'])

        self._add_label("Connection options:", row=9, column=2, columnspan=4)

        rb_once = tk.Radiobutton(self.root, text="Connect once",
                                 variable=self.variables['con_mode'],
                                 value="con_once",
                                 **self.colors)
        rb_once.grid(row=10, column=2, sticky=tk.W)

        rb_per = tk.Radiobutton(self.root, text="Connect per send",
                                variable=self.variables['con_mode'],
                                value="con_per",
                                **self.colors)
        rb_per.grid(row=11, column=2, sticky=tk.W)

        self._add_label("Max. retries:", row=10, column=4, sticky=tk.W)
        self._add_entry('max_retries', width=2, row=10, column=5, sticky=tk.W)

    def spawn_gui_menubar(self):
        """Spawns the GUI menu bar that runs along the top of the
        window."""
        menu = tk.Menu(self.root)

        menu_email = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label='Email', menu=menu_email)

        menu_email.add_command(label="Send",
                               command=self.coordinator.callbacks['send'])
        menu_email.add_command(label="Edit headers",
                               command=self.coordinator.callbacks['headers'])

        menu_settings = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label='Settings', menu=menu_settings)

        menu_settings.add_command(label="Auto-select multithreading",
            command=self.coordinator.callbacks['autoselectmt'])

        menu_help = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label='Help', menu=menu_help)

        menu_help.add_command(label="Brief help",
                              command=self.coordinator.callbacks['quickhelp'])
        menu_help.add_command(label="In-depth documentation (online)",
                              command=self.coordinator.callbacks['deephelp'])

        self.root.config(menu=menu)
