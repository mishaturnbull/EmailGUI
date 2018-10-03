# -*- coding: utf-8 -*-
"""
Holds the GUI callback functions.
"""

import sys
import webbrowser

from helpers import suggest_thread_amt
from prereqs import GUI_DOC
from header_gui import HeaderGUI

if sys.version_info.major == 3:
    import tkinter as tk
    import tkinter.messagebox as messagebox
    import tkinter.filedialog as filedialog
    import tkinter.scrolledtext as scrolledtext
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
    coordinator.gui.bar['maximum'] = coordinator.settings['amount']
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

    coordinator.retrieve_data_from_uis()

    prev_serv = None

    try:
        settings = suggest_thread_amt(coordinator)
    except ValueError:
        # most likely a server address that couldn't be determined to be
        # local or nonlocal
        # ask the user and do some tinkering ;)
        ans = messagebox.askyesnocancel("Settings auto-selection",
                                        "Unable to determine if the server "
                                        "is local or not!  Please select "
                                        "whether or not the specified "
                                        "server is running locally or not.")
        if ans is None:
            # simplest case -- None is returned on cancel.
            return
        elif ans:
            # user said yes
            prev_serv = coordinator.settings['server']
            coordinator.settings['server'] = '127.0.0.1'
        else:
            # user said no
            prev_serv = coordinator.settings['server']
            coordinator.settings['server'] = '134.129.156.163'

        settings = suggest_thread_amt(coordinator)
        coordinator.settings['server'] = prev_serv

    for key in settings:
        coordinator.settings[key] = settings[key]

    coordinator.gui.pull_values_from_coordinator()


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
