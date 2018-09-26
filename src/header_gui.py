# -*- coding: utf-8 -*-
"""
Contains the header edit submenu.
"""

from gui import GUIBase

import sys

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

class HeaderGUI(GUIBase):
    
    def __init__(self, coordinator):
        """Instantiate the header menu."""
        super(HeaderGUI, self).__init__(coordinator, coordinator.gui.root)
        
        self.entry_width = self.entry_width // 3
        
        self.max_rows = 4
    
    def _add_entry(self, varname, width=None, entry_opts=None, **grids):
        """Wrapper for GUIBase's _add_entry method.  Autofills from the
        header sub-dictionary in contents."""
        super(HeaderGUI, self)._add_entry(varname, width, entry_opts, **grids)
        self.variables[varname].set(
                self.coordinator.contents['headers'][varname])
    
    def _add_box(self, name, label, box_opts=None, **grids):
        """Wrapper for GUIBase's _add_box method.  Auto-enables if the 
        corresponding header is enabled."""
        super(HeaderGUI, self)._add_box(name, label, box_opts, **grids)
        entryname = name.split('_')[1]
        if entryname in self.variables:
            headerval = self.variables[entryname].get()
            if headerval != '':
                ename = 'enable_' + entryname
                print('setting {} to 1...'.format(ename))
                v = self.variables[ename]
                print('variable: ' + repr(v))
                v.set(1)
                print('value: ' + str(v.get()))

    def spawn_gui_basics(self):
        """Spawn the base parts of the GUI."""
        
        self.root.wm_title("Edit Headers")
        self.root.config(**self.colors)
        
        row = column = 0
        
        for header in self.coordinator.contents['headers']:
            self._add_entry(header, row=row, column=column+1, sticky=tk.W)
            self._add_box("enable_" + header, header.capitalize() + ":",
                          row=row, column=column, sticky=tk.W)
            
            row += 1
            if row >= self.max_rows:
                row = 0
                column += 2
        