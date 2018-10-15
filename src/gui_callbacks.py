# -*- coding: utf-8 -*-
"""
Holds the GUI callback functions.
"""

import sys
import webbrowser
import traceback

from helpers import suggest_thread_amt
from prereqs import GUI_DOC
from helper_guis import HeaderGUI, VerificationGUI, EmailEditorGUI
from gui_addons import error_more_details
from emailbuilder import PayloadGenerator

if sys.version_info.major == 3:
    import tkinter as tk
    import tkinter.messagebox as messagebox
    import tkinter.filedialog as filedialog
    import tkinter.scrolledtext as scrolledtext
    import tkinter.simpledialog as simpledialog
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
    import tkSimpleDialog as simpledialog


CALLBACKS = []


def handle_verify(coordinator):
    """Spawn the verification window and handle the attempts to verify an
    address."""
    vgui = VerificationGUI(coordinator)
    vgui.build_gui()


CALLBACKS.append(handle_verify)


def handle_abort(coordinator):
    """Deal with an abort button call."""
    coordinator.sender.abort()


CALLBACKS.append(handle_abort)


def handle_browse(coordinator):
    """Handle a request to browse the filesystem."""
    coordinator.gui.root.grab_set()
    filename = filedialog.askopenfilename()
    var = coordinator.gui.variables['attachments']
    if var.get() == '':
        var.set(filename)
    else:
        var.set(var.get() + "," + filename)


CALLBACKS.append(handle_browse)


def handle_send(coordinator):
    """Send the emails."""
    if coordinator.settings['debug']:
        print("recieved send instruction, beginning firing sequence")
    try:
        coordinator.prepare_to_send()
    except RuntimeError as exc:
        if exc.args[0].startswith("Currently not ready to send"):
            coordinator.callbacks['reset']()
            coordinator.prepare_to_send()
        else:
            raise  # error was something else
    coordinator.gui.bar['maximum'] = coordinator.settings['amount']
    msg = '\n'.join(coordinator.settings['confirmation_msg'])
    coordinator.gui.root.grab_set()
    mboxres = messagebox.askyesno("Confirmation", msg)
    if mboxres:
        coordinator.gui._notebook.select(".!notebook.!frame3")
        coordinator.send()


CALLBACKS.append(handle_send)


def handle_reset(coordinator):
    """Reset the program for another round of sending."""
    coordinator.reset()
    coordinator.gui.variables['progressbar'].set(0)
    coordinator.gui.reset_subprogress_bars()
    coordinator.ready_to_send = True


CALLBACKS.append(handle_reset)


def handle_headers(coordinator):
    """Spawn the header GUI."""
    coordinator.retrieve_data_from_uis()
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
        coordinator.gui.root.grab_set()
        ans = messagebox.askyesnocancel("Settings auto-selection",
                                        "Unable to determine if the server "
                                        "is local or not!  Please select "
                                        "whether or not the specified "
                                        "server is running locally or not."
                                        "  If you don't know what this means,"
                                        " select no.")
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


def handle_flushlogs(coordinator):
    """Dump log information."""
    sys.stdout.dump_logs()
    sys.stderr.dump_logs()


CALLBACKS.append(handle_flushlogs)


def handle_emailEditWindow(coordinator):
    """Spawn the more in-depth email editor."""
    egui = EmailEditorGUI(coordinator)
    egui.spawn_gui_elements()
    egui.sync_from_main()


CALLBACKS.append(handle_emailEditWindow)


def handle_addRandomPayload(coordinator):
    """Prompt for payload size and add a random text payload."""
    editor = coordinator.active_guis['editor']
    editor.root.grab_set()
    nbytes = simpledialog.askinteger("Add Payload",
                                     "How many bytes should the payload be?",
                                     parent=editor.root)
    text = PayloadGenerator(coordinator).get_random_text(nbytes)
    coordinator.email.add_text(text)


CALLBACKS.append(handle_addRandomPayload)


# don't add this to CALLBACKS
def handle_error(coordinator):
    """Display an error message for the user."""
    tp, val, trace = sys.exc_info()
    coordinator.gui.root.grab_set()
    if error_more_details(type(tp), val.args[0], coordinator.gui.root):
        helper = tk.Toplevel(coordinator.gui.root)
        helper.title("Error occurred")
        txt = scrolledtext.ScrolledText(helper)
        excmsg = traceback.format_tb(trace)
        txt.insert(tk.END, excmsg)
        txt['font'] = ('liberation mono', '10')
        txt.pack(expand=True, fill='both')
