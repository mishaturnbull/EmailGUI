# -*- coding: utf-8 -*-
"""
Holds the GUI callback functions.
"""

import sys
import webbrowser

from helpers import suggest_thread_amt, verify_to, verify_to_email
from prereqs import GUI_DOC
from header_gui import HeaderGUI

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


CALLBACKS = []


def handle_verify(coordinator):
    """Spawn the verification window and handle the attempts to verify an
    address."""
    root = coordinator.gui.root
    vmen = tk.Toplevel(root)
    vmen.config(**coordinator.gui.colors)
    vmen.title("Email Verification")
    # TODO: finish verify menu
CALLBACKS.append(handle_verify)


def handle_abort(coordinator):
    """Deal with an abort button call."""
    coordinator.sender.abort()
CALLBACKS.append(handle_abort)


def handle_browse(coordinator):
    """Handle a request to browse the filesystem."""
    filename = filedialog.askopenfilename()
    var = coordinator.gui.variables['attachments']
    if var.get() == '':
        var.set(filename)
    else:
        var.set(var.get() + "," + filename)
CALLBACKS.append(handle_browse)


def handle_send(coordinator):
    """Send the emails."""
    msg = '\n'.join(coordinator.settings['confirmation_msg'])
    mboxres = messagebox.askyesno("Confirmation", msg)
    if mboxres:
        coordinator.send()
CALLBACKS.append(handle_send)


def handle_headers(coordinator):
    """Spawn the header GUI."""
    hgui = HeaderGUI(coordinator)
    hgui.spawn_gui_basics()
    
CALLBACKS.append(handle_headers)


def handle_autoselectmt(coordinator):
    """Automatically select the multithreading and connection options."""
    num_emails = int(coordinator.gui.variables['amount'].get())
    mode, field, conmode = suggest_thread_amt(num_emails)
    
    if mode == 'none':
        coordinator.gui.variables['delay'].set(str(field))
    elif mode == 'limited':
        coordinator.gui.variables['mt_num'].set(str(field))
    
    coordinator.gui.variables['mt_mode'].set(mode)
    coordinator.gui.variables['con_mode'].set(str(conmode))
CALLBACKS.append(handle_autoselectmt)


def handle_quickhelp(coordinator):
    """In-program GUI documentation."""
    
    helper = tk.Toplevel(coordinator.gui.root)
    helper.title("Help")
    txt = scrolledtext.ScrolledText(helper)
    txt.insert(tk.END, GUI_DOC)
    txt['font'] = ('liberation mono', '10')
    txt.pack(expand=True, fill='both')
CALLBACKS.append(handle_quickhelp)


def handle_deephelp(coordinator):
    """Take the user online for help."""
    webbrowser.open("https://mishaturnbull.github.io/EmailGUI/index.html")
CALLBACKS.append(handle_deephelp)