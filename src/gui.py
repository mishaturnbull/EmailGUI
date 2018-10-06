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
import threading

from gui_addons import Tooltip

if sys.version_info.major == 3:
    import tkinter as tk
    from tkinter import ttk
elif sys.version_info.major == 2:
    # pylint: disable=E0401
    # pylint complains about not finding tkMessageBox etc
    #  when run using python 3, because this stuff is for python 2
    #  but this block will never be executed in py3, and therefore
    #  will never throw an error
    import Tkinter as tk
    import ttk


class GUIBase(object):
    """Base class for a GUI.  Not to be called to directly."""

    def __init__(self, coordinator, _root=None):
        """Instantiate the GUI."""

        self.coordinator = coordinator

        if _root is None:
            self.root = tk.Tk()
        else:
            self.root = tk.Toplevel(_root)

        self.variables = self.boxes = {}
        self.entry_width = self.coordinator.settings['width']

        if 'colors' not in self.coordinator.settings:
            self.colors = self.buttons = {}
            return

        self.colors = {"background": self.coordinator.settings['colors']['bg'],
                       }
        self.buttons = {"background":
                        self.coordinator.settings['colors']['buttons'],
                        "activebackground":
                            self.coordinator.settings['colors']['bg'],
                        }

    def _add_label(self, text, root=None, label_opts=None, **grids):
        """Adds a tk.Label element to the root window and grids it
        using the **args provided."""
        if label_opts is None:
            label_opts = {}
        if root is None:
            root = self.root
        lbl = tk.Label(root, text=text, **label_opts,
                       **self.colors).grid(**grids)
        return lbl

    def _add_entry(self, varname, root=None, width=None, entry_opts=None,
                   **grids):
        """Adds a tk.Entry element to the root window, adds the variable
        to the variables dictionary, and grids it to the window."""
        if entry_opts is None:
            entry_opts = {}
        if width is None:
            width = self.entry_width
        if width is not None:
            entry_opts.update({'width': width})
        if root is None:
            root = self.root
        var = tk.StringVar()
        self.variables.update({varname: var})
        entry = tk.Entry(root, textvariable=var, **entry_opts)
        entry.grid(**grids)

        # check for any default options under the varname
        if varname in self.coordinator.contents:
            var.set(self.coordinator.contents[varname])
        if varname in self.coordinator.settings:
            var.set(self.coordinator.settings[varname])

        return entry

    def _add_button(self, label, callback, root=None, btn_opts=None, **grids):
        """Adds a tk.Button element to the root window, configures it,
        and grids it to the root."""
        if btn_opts is None:
            btn_opts = {}
        if root is None:
            root = self.root
        btn = tk.Button(root, text=label, command=callback,
                        **btn_opts, **self.colors)
        btn.grid(**grids)
        return btn

    def _add_box(self, name, label, root=None, box_opts=None, **grids):
        """Adds a checkbox to the GUI with specified name and options."""
        if box_opts is None:
            box_opts = {}
        if root is None:
            root = self.root
        self.variables.update({name: tk.IntVar()})
        self.variables[name].set(0)

        box = tk.Checkbutton(root, text=label,
                             variable=self.variables[name],
                             **box_opts, **self.colors)
        box.grid(**grids)

        if name in self.coordinator.contents:
            self.variables[name].set(int(self.coordinator.contents[name]))
        if name in self.coordinator.settings:
            self.variables[name].set(int(self.coordinator.settings[name]))
        return box

    def dump_values_to_coordinator(self):
        """Sends over all the information needed for a successful email."""
        if self.coordinator.settings['debug']:
            print("guibase.dump_values_to_coordinator: beginning data dump")
        for var in self.variables:
            if self.coordinator.settings['debug']:
                print("  processing " + var + " with " + repr(
                    self.variables[var].get()))

            if var in self.coordinator.settings:
                dic = self.coordinator.settings
            elif var in self.coordinator.contents:
                dic = self.coordinator.contents
            else:
                # stuff like progressbar we don't want to add to variables
                continue

            try:
                val = float(self.variables[var].get())

                # check for and remove unneeded decimals, e.g.:
                # 2.0 -> 2, this way we can call range() on it later
                if int(val) == val:
                    val = int(val)
            except (ValueError, TypeError):
                try:
                    val = int(self.variables[var].get())
                except (ValueError, TypeError):
                    val = self.variables[var].get()

            if self.coordinator.settings['debug']:
                print("  dumping variable " + var + " with value " + str(val))
            dic[var] = val

    def pull_values_from_coordinator(self):
        """Update (and overwrite!) all values with those stored in the
        coordinator."""
        if self.coordinator.settings['debug']:
            print('guibase.pull_values_from_coordinator: beginning data pull')

        for key in self.variables:
            if self.coordinator.settings['debug']:
                print('   processing ' + str(key) + " with val " +
                      repr(self.variables[key].get()))

            if key in self.coordinator.settings:
                dsel = self.coordinator.settings
            elif key in self.coordinator.contents:
                dsel = self.coordinator.contents
            else:
                continue

            val = str(dsel[key])
            self.variables[key].set(val)

    def run(self):
        """Starts the GUI."""

        self.root.mainloop()


class EmailGUI(GUIBase):
    '''Make things easier to use, and prettier.'''

    def __init__(self, coordinator):
        '''Start the class, and make stuff happen.'''
        super(EmailGUI, self).__init__(coordinator)

        self._pbar_lock = threading.Lock()
        # pylint: disable=C0102
        self.bar = None

    def callback_sent(self):
        """Action to take on a sent email."""
        # progress bar update
        self._pbar_lock.acquire()
        var = self.variables['progressbar']
        var.set(var.get() + 1)
        self._pbar_lock.release()

    def spawn_gui(self):
        """Spawn the entire GUI."""
        self.spawn_gui_basics()
        self.spawn_gui_notebook()
        self.spawn_gui_menubar()

    def spawn_gui_basics(self):
        """Instantiate all the GUI elements.  Does not spawn the GUI."""

        # start with the window meta
        self.root.title(self.coordinator.settings['title'])

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

    def spawn_gui_notebook(self):
        """Create the notebook pages."""
        notebook = ttk.Notebook(self.root)
        notebook.grid(row=10, column=0, columnspan=10, sticky='nsew')

        self.spawn_page_1(notebook)
        self.spawn_page_2(notebook)

    def spawn_page_1(self, notebook):
        """Create the elements of the first tab page."""

        page = tk.Frame(notebook, **self.colors)
        notebook.add(page, text="Sending", compound=tk.TOP)

        mtframe = tk.LabelFrame(page, text="Multithreading options",
                                relief=tk.RIDGE, **self.colors)
        mtframe.grid(row=0, column=1, sticky='w',)

        self.variables.update({"mt_mode": tk.StringVar()})
        self.variables['mt_mode'].set(self.coordinator.settings['mt_mode'])

        rb_none = tk.Radiobutton(mtframe, text="None",
                                 variable=self.variables['mt_mode'],
                                 value="none",
                                 **self.colors)
        rb_none.grid(row=0, column=0, sticky='nw')

        rb_lim = tk.Radiobutton(mtframe, text="Limited",
                                variable=self.variables['mt_mode'],
                                value='limited',
                                **self.colors)
        rb_lim.grid(row=1, column=0, sticky='nw')

        rb_ulim = tk.Radiobutton(mtframe, text="Unlimited",
                                 variable=self.variables['mt_mode'],
                                 value="unlimited",
                                 **self.colors)
        rb_ulim.grid(row=2, column=0, sticky='nw')

        self._add_entry('delay', root=mtframe, width=4,
                        row=0, column=1, sticky='nw')
        self._add_entry('mt_num', root=mtframe, width=4,
                        row=1, column=1, sticky='nw')


        oframe = tk.LabelFrame(page, text="Misc. options",
                               relief=tk.RIDGE, **self.colors)
        oframe.grid(row=0, column=2, sticky='nw')

        dbgbox = self._add_box("debug", "Debug mode", root=oframe,
                               row=0, column=0, sticky=tk.W)
        Tooltip(dbgbox, text="Not recommended!  Makes program slow!")
        
        rtlbox = self._add_box("realtime", "Realtime logging", root=oframe,
                               row=1, column=0, sticky=tk.W)
        Tooltip(rtlbox, text="Not recomended!  Makes program very slow!")
        
        self._add_button("Dump logs",
                         self.coordinator.callbacks['flushlogs'],
                         root=oframe, row=2, column=0, sticky='w')

        bframe = tk.LabelFrame(page, text="Controls",
                               relief=tk.RIDGE, **self.colors)
        bframe.grid(row=0, column=0, sticky='nw')

        self._add_button('Send', self.coordinator.callbacks['send'],
                         root=bframe, row=0, column=0, sticky='n')
        self._add_button('Abort', self.coordinator.callbacks['abort'],
                         root=bframe, row=1, column=0, sticky='n')
        self._add_button('Reset', self.coordinator.callbacks['reset'],
                         root=bframe, row=2, column=0, sticky='n')

        # progress bar
        # no helper function here :(
        self._add_label("Progress:", root=page, row=4, column=0, sticky=tk.W)
        self.variables.update({'progressbar': tk.IntVar()})
        # pylint: disable=C0102
        # "Blacklisted name 'bar'"
        # In this case, 'bar' makes perfect sense and is not
        # being used as in foo/bar/baz
        self.bar = ttk.Progressbar(page, orient='horizontal', length=600,
                                   mode='determinate',
                                   variable=self.variables['progressbar'],
                                   maximum=self.coordinator.settings['amount'])
        self.bar.grid(row=4, column=1, columnspan=9, sticky=tk.W)

    def spawn_page_2(self, notebook):
        """Spawn the page with connection options."""

        page = tk.Frame(notebook, **self.colors)
        notebook.add(page, text="Connection", compound=tk.TOP)

        cframe = tk.LabelFrame(page, text="Connection options",
                               relief=tk.RIDGE, **self.colors)
        cframe.grid(row=9, column=2, rowspan=3, columnspan=4,
                    padx=30, pady=4, sticky='w')

        self.variables.update({'con_mode': tk.StringVar()})
        self.variables['con_mode'].set(self.coordinator.settings['con_mode'])

        rb_once = tk.Radiobutton(cframe, text="Connect once",
                                 variable=self.variables['con_mode'],
                                 value="con_once",
                                 **self.colors)
        rb_once.grid(row=0, column=0, sticky=tk.W)

        rb_per = tk.Radiobutton(cframe, text="Connect per send",
                                variable=self.variables['con_mode'],
                                value="con_per",
                                **self.colors)
        rb_per.grid(row=1, column=0, sticky=tk.W)

        rb_some = tk.Radiobutton(cframe, text="Connect every n mails:",
                                 variable=self.variables['con_mode'],
                                 value="con_some",
                                 **self.colors)
        rb_some.grid(row=2, column=0, sticky=tk.W)
        self._add_entry("con_num", root=cframe, width=4,
                        row=2, column=1, sticky=tk.W)

        self._add_label("Max. retries:", root=cframe, row=0,
                        column=2, sticky=tk.W)
        self._add_entry('max_retries', root=cframe,
                        width=4, row=0, column=3, sticky=tk.W)

        self._add_box("wait_on_retry", "Wait for connection",
                      root=cframe, row=1, column=2, sticky=tk.W)
        self._add_entry("wait_dur_on_retry",
                        root=cframe, width=4, row=1, column=3,
                        sticky=tk.W)

    def spawn_gui_menubar(self):
        """Spawns the GUI menu bar that runs along the top of the
        window."""
        menu = tk.Menu(self.root)

        menu_email = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label='Email', menu=menu_email)

        menu_email.add_command(label="Edit headers",
                               command=self.coordinator.callbacks['headers'])

        menu_settings = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label='Settings', menu=menu_settings)

        menu_settings.add_command(label="Auto-select multithreading",
                                  command=self.coordinator.callbacks[
                                      'autoselectmt'])

        menu_help = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label='Help', menu=menu_help)

        menu_help.add_command(label="Brief help",
                              command=self.coordinator.callbacks['quickhelp'])
        menu_help.add_command(label="In-depth documentation (online)",
                              command=self.coordinator.callbacks['deephelp'])

        self.root.config(menu=menu)
