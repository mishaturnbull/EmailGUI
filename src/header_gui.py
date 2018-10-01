# -*- coding: utf-8 -*-
"""
Contains the header edit submenu.
"""

import sys

from gui import GUIBase

if sys.version_info.major == 3:
    import tkinter as tk
elif sys.version_info.major == 2:
    import Tkinter as tk

class HeaderGUI(GUIBase):
    """This class is responsible for the GUI that allows the user to 
    enter/alter different email headers."""

    def __init__(self, coordinator):
        """Instantiate the header menu."""
        super(HeaderGUI, self).__init__(coordinator, coordinator.gui.root)

        self.entry_width = self.entry_width // 3

        self.max_rows = 4

        self.root.protocol("WM_DELETE_WINDOW", self.close_action)

    def _add_entry(self, varname, width=None, entry_opts=None, **grids):
        """Wrapper for GUIBase's _add_entry method.  Autofills from the
        header sub-dictionary in contents."""
        super(HeaderGUI, self)._add_entry(varname, width, entry_opts, **grids)
        self.variables[varname].set(
            self.coordinator.headers.headers[varname])

    def _add_box(self, name, label, box_opts=None, **grids):
        """Wrapper for GUIBase's _add_box method.  Auto-enables if the
        corresponding header is enabled."""
        super(HeaderGUI, self)._add_box(name, label, box_opts, **grids)
        entryname = name.split('_')[1]
        if entryname in self.variables:
            headerval = self.variables[entryname].get()
            if headerval != '':
                self.variables['enable_' + entryname].set(1)

    def close_action(self):
        """Close the window."""
        self.dump_values_to_headers()
        self.root.destroy()

    def dump_values_to_headers(self):
        """Output the values to the header class."""
        self.coordinator.headers.pull_from_header_gui(self)

    def spawn_gui_basics(self):
        """Spawn the base parts of the GUI."""

        self.root.wm_title("Edit Headers")
        self.root.config(**self.colors)

        row = column = 0

        for header in self.coordinator.headers.headers:
            self._add_entry(header, row=row, column=column+1, sticky=tk.W)
            self._add_box("enable_" + header, header.capitalize() + ":",
                          row=row, column=column, sticky=tk.W)

            row += 1
            if row >= self.max_rows:
                row = 0
                column += 2
