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
import uuid

from gui_addons import Tooltip
from helpers import time_from_epoch

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

    def __init__(self, coordinator, _root=None, name=None):
        """Instantiate the GUI."""

        self.coordinator = coordinator
        self.name = name or uuid.uuid4()
        self.coordinator.register_gui_state_change(self.name, self, 'active')

        if _root is None:
            self.root = tk.Tk()
        else:
            self.root = tk.Toplevel(_root)
        self.root.resizable(False, False)

        self.variables = self.boxes = {}
        self.entry_width = self.coordinator.settings['width']

        if 'colors' not in self.coordinator.settings:
            self.colors = self.buttons = {}
        else:
            self.colors = {"background":
                           self.coordinator.settings['colors']['bg'],
                           }
            self.buttons = {"background":
                            self.coordinator.settings['colors']['buttons'],
                            "activebackground":
                                self.coordinator.settings['colors']['bg'],
                            }

        self.root.protocol("WM_DELETE_WINDOW", self._close_action)
    
    def _configure_style(self):
        """Setup the Tkinter style."""
        s = ttk.Style()
        s.theme_use('clam')
        

    def _close_action(self):
        """Calls the custom close actions then destroys the window."""
        self.close_action()
        self.coordinator.register_gui_state_change(self.name, self, 'inactive')
        self.root.destroy()

    def close_action(self):
        """To be overriden by subclasses."""
        pass

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
                    self.variables[var].get()) + "/" + repr(type(
                        self.variables[var].get())))

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

            if isinstance(self.variables[key], tk.IntVar):
                val = int(dsel[key])
            elif isinstance(self.variables[key], tk.StringVar):
                val = str(dsel[key])
            self.variables[key].set(val)

    def run(self):
        """Starts the GUI."""

        self.root.mainloop()


class EmailGUI(GUIBase):
    '''Make things easier to use, and prettier.'''

    def __init__(self, coordinator):
        '''Start the class, and make stuff happen.'''
        super(EmailGUI, self).__init__(coordinator, name='main')

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
        self._add_label("# Emails:", row=0, column=0, sticky='w')
        self._add_entry('amount', width=3, row=0, column=1, sticky='ew')

        # to field
        self._add_label("Recipient(s):", row=1, column=0, sticky='w')
        self._add_button("Verify", self.coordinator.callbacks['verify'],
                         row=1, column=1)
        self._add_entry('to', row=1, column=2, columnspan=8,
                        sticky='ew')

        # from field
        self._add_label("Sender(s):", row=2, column=0, sticky='w')
        self._add_entry('account', row=2, column=1, columnspan=9,
                        sticky='ew')

        # password field
        self._add_label("Password(s):", row=3, column=0, sticky='w')
        self._add_entry('password', entry_opts={'show': '*'},
                        row=3, column=1, columnspan=9, sticky='ew')

        # subject field
        self._add_label("Subject line:", row=4, column=0, sticky='w')
        self._add_entry('subject', row=4, column=1, columnspan=9,
                        sticky='ew')

        # text field
        self._add_label("Email message:", row=5, column=0, sticky='w')
        self._add_button("Edit", self.coordinator.callbacks['emailEditWindow'],
                         row=5, column=1)
        self._add_entry('text', row=5, column=2, columnspan=8,
                        sticky='ew')

        # server
        self._add_label("Server:", row=6, column=0, sticky='w')
        self._add_entry('server', row=6, column=1, columnspan=9,
                        sticky='ew')

        # attachments
        self._add_label("Attachments:", row=7, column=0, sticky='w')
        self._add_button("Browse", self.coordinator.callbacks['browse'],
                         row=7, column=1)
        self._add_entry('attachments', row=7, column=2, columnspan=8,
                        sticky='ew')

    def spawn_gui_notebook(self):
        """Create the notebook pages."""
        self._notebook = ttk.Notebook(self.root)
        self._notebook.grid(row=10, column=0, columnspan=10, sticky='nsew')

        self.spawn_page_1(self._notebook)
        self.spawn_page_2(self._notebook)
        self.spawn_page_3(self._notebook)

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
                               row=0, column=0, sticky='w')
        Tooltip(dbgbox, text="Not recommended!  Makes program slow!")

        rtlbox = self._add_box("realtime", "Realtime logging", root=oframe,
                               row=1, column=0, sticky='w')
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

    def spawn_page_2(self, notebook):
        """Spawn the page with connection options."""

        page = tk.Frame(notebook, **self.colors)
        notebook.add(page, text="Connection", compound=tk.TOP)

        cframe = tk.LabelFrame(page, text="Connection options",
                               relief=tk.RIDGE, **self.colors)
        cframe.grid(row=0, column=0, rowspan=3, columnspan=4,
                    padx=30, pady=4, sticky='w')

        aframe = tk.LabelFrame(page, text="Protocol options",
                               relief=tk.RIDGE, **self.colors)
        aframe.grid(row=0, column=4, rowspan=3, columnspan=2,
                    padx=30, pady=4, sticky='w')

        self.variables.update({'con_mode': tk.StringVar()})
        self.variables['con_mode'].set(self.coordinator.settings['con_mode'])

        rb_once = tk.Radiobutton(cframe, text="Connect once",
                                 variable=self.variables['con_mode'],
                                 value="con_once",
                                 **self.colors)
        rb_once.grid(row=0, column=0, sticky='w')

        rb_per = tk.Radiobutton(cframe, text="Connect per send",
                                variable=self.variables['con_mode'],
                                value="con_per",
                                **self.colors)
        rb_per.grid(row=1, column=0, sticky='w')

        rb_some = tk.Radiobutton(cframe, text="Connect every n mails:",
                                 variable=self.variables['con_mode'],
                                 value="con_some",
                                 **self.colors)
        rb_some.grid(row=2, column=0, sticky='w')
        self._add_entry("con_num", root=cframe, width=4,
                        row=2, column=1, sticky='w')

        self._add_label("Max. retries:", root=cframe, row=0,
                        column=2, sticky='w')
        self._add_entry('max_retries', root=cframe,
                        width=4, row=0, column=3, sticky='w')

        self._add_box("wait_on_retry", "Wait for connection",
                      root=cframe, row=1, column=2, sticky='w')
        self._add_entry("wait_dur_on_retry",
                        root=cframe, width=4, row=1, column=3,
                        sticky='w')

        tls = self._add_box("use_starttls", "Use STARTTLS",
                            root=aframe, row=0, column=0, sticky='w')
        Tooltip(tls, text="Use STARTTLS if server allows it.")

        auth = self._add_box("use_auth", "Use AUTH",
                             root=aframe, row=1, column=0, sticky='w')
        Tooltip(auth, text="Use AUTH if server allows it.")
    
    def spawn_page_3(self, notebook):
        """Spawn the progress page"""
        page = tk.Frame(notebook)
        notebook.add(page, text="Progress", compound=tk.TOP)
        
        self.barframe = tk.Frame(page)
        self.barframe.grid(row=0, column=0, columnspan=10, sticky='nsew')
        self._add_label("Sub-progress bars will spawn once emails are sent!",
                        root=self.barframe, row=0, column=0, 
                        columnspan=10, sticky='nsew')
        
        # progress bar
        # no helper function here :(
        self.variables.update({'progressbar': tk.IntVar()})
        # pylint: disable=C0102
        # "Blacklisted name 'bar'"
        # In this case, 'bar' makes perfect sense and is not
        # being used as in foo/bar/baz
        self.bar = ttk.Progressbar(page, orient='horizontal', length=600,
                                   mode='determinate',
                                   variable=self.variables['progressbar'],
                                   maximum=self.coordinator.settings['amount'])
        self.bar.grid(row=1, column=0, columnspan=10, sticky='w')
        
        self._add_label("#Remaining: ", root=page, row=2, column=0, sticky='w')
        self._add_changinglabel("0", 'remaining', root=page, row=2,
                                column=1, sticky='w')
        self._add_label("Sent: ", root=page, row=2, column=2, sticky='w')
        self._add_changinglabel("0", 'sent', root=page, row=2,
                                column=3, sticky='w')
        self._add_label("Time Remaining: ", root=page, row=2, column=4,
                        sticky='w')
        self._add_changinglabel("00:00", 'etr', root=page, row=2,
                                column=5, sticky='w')
        self._add_label("E.T.C:", root=page, row=2, column=6, sticky='w')
        self._add_changinglabel("00:00", 'etc', root=page, row=2,
                                column=7, sticky='w')
        ################### ROW SPLIT
        self._add_label("Mail/sec: ", root=page, row=3, column=0, sticky='w')
        self._add_changinglabel('0', 'sending-rate', root=page, row=3,
                                column=1, sticky='w')
        self._add_label("Time for 1 mail:", root=page, row=3, column=2,
                        sticky='w')
        self._add_changinglabel('0', 'sending-time', root=page, row=3,
                                column=3, sticky='w')
        self._add_label("Active connections:", root=page, row=3, column=4,
                        sticky='w')
        self._add_changinglabel("0", 'no-active-connections', root=page,
                                row=3, column=5, sticky='w')
    
    def pull_metrics_from_coordinator(self):
        """Grab the metrics from the coordinator, convert to UX-friendly
        format, and push to display."""
        
        def rstr(num):
            return str(round(num, 2))
        
        direct_translations = ['remaining', 'sent', 'no-active-connections']
        for t in direct_translations:
            self.variables[t].set(str(self.coordinator.metrics[t]))
        self.variables['etr'].set(
                time_from_epoch(self.coordinator.metrics['etr'],
                                tzconvert=False))
        self.variables['etc'].set(
                time_from_epoch(self.coordinator.metrics['etc']))
        self.variables['sending-rate'].set(
                rstr(self.coordinator.metrics['sending-rate']) + " / sec")
        self.variables['sending-time'].set(
                rstr(self.coordinator.metrics['sending-time']) + " sec")
    
    def add_n_progress_bars(self, n):
        """Add a number of progress bars to the progress window.
        Will autofill from coordinator settings with relevant information,
        but must be given the number of bars to spawn.
        
        By the time this is called, coordinator.sender.worker_amounts
        must be defined and accurate.
        
        Returns a list of ttk.Progressbar's."""
        amounts = self.coordinator.sender.worker_amounts
        bars = []
        intvars = []
        length = int(600 / n)
        
        for i in range(n):
            var = tk.IntVar()
            var.set(0)
            intvars.append(var)
            newbar = ttk.Progressbar(self.barframe, orient='horizontal',
                                     length=length, mode='indeterminate',
                                     variable=var,
                                     maximum=amounts[i])
            newbar.grid(row=0, column=i, sticky='w')
            bars.append(newbar)
        
        return bars, intvars
    
    def reset_subprogress_bars(self):
        """Resets the thread progress bars."""
        page = self.barframe.master
        self.barframe.destroy()
        self.barframe = tk.Frame(page)
        self.barframe.grid(row=0, column=0, columnspan=10, sticky='nsew')
        self._add_label("Sub-progress bars will spawn once emails are sent!",
                        root=self.barframe, row=0, column=0, 
                        columnspan=10, sticky='nsew')

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
