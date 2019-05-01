# -*- coding: utf-8 -*-
"""
Contains the header edit submenu.
"""

import sys
import re

from gui import GUIBase
from gui_addons import Tooltip
from helpers import verify_to, verify_to_email, check_rfc_5322

if sys.version_info.major == 3:
    import tkinter as tk
    from tkinter import simpledialog
    from tkinter import scrolledtext
    import tkinter.ttk as ttk
elif sys.version_info.major == 2:
    import Tkinter as tk
    import tkSimpleDialog as simpledialog
    import tkScrolledText as scrolledtext
    import ttk


class HeaderGUI(GUIBase):
    """This class is responsible for the GUI that allows the user to
    enter/alter different email headers."""

    def __init__(self, coordinator):
        """Instantiate the header menu."""
        super(HeaderGUI, self).__init__(coordinator, coordinator.gui.root,
                                        name='headers')

        self.variables = []

        self.entry_width = self.entry_width // 3

        self._max_rows = 10
        self._row = 1
        self._column = 0

        self.leftside = self.rightside = None  # defined later in gui basics

    def _add_entry(self, idx, root=None, width=None, entry_opts=None,
                   **grids):
        """Wrapper for GUIBase's _add_entry method.  Autofills from the
        header sub-dictionary in contents."""
        entry_opts = entry_opts or {}
        width = width or self.entry_width
        entry_opts.update(width=width)
        root = root or self.root

        self.variables[idx]['value'] = tk.StringVar()
        if self.variables[idx]['name'] in self.coordinator.headers.header_list:
            # vagrant syntax abuse, but necessary to keep this from being
            # 9000 characters long
            name = self.variables[idx]['name']
            hlidx = self.coordinator.headers.header_list.index(name)
            hlinfo = self.coordinator.headers.headers[hlidx]
            value = hlinfo['value']
            self.variables[idx]['value'].set(value)

        entry = tk.Entry(root, textvariable=self.variables[idx]['value'],
                         **entry_opts)
        entry.grid(**grids)

        return entry

    def _add_box(self, idx, label, root=None, box_opts=None, **grids):
        """Wrapper for GUIBase's _add_box method.  Auto-enables if the
        corresponding header is enabled."""
        box_opts = box_opts or {}
        root = root or self.root

        self.variables[idx]['enabled'] = tk.IntVar()
        if self.variables[idx]['value'].get() is not '':
            self.variables[idx]['enabled'].set(1)

        box = tk.Checkbutton(root, text=label,
                             variable=self.variables[idx]['enabled'],
                             **box_opts, **self.colors)
        box.grid(**grids)

        return box

    def close_action(self):
        """Close the window."""
        self.dump_values_to_headers()

    def dump_values_to_headers(self):
        """Output the values to the header class."""
        self.coordinator.headers.pull_from_header_gui(self)

    # copied from headers
    # TODO: possible to add a cache of some sort here?
    # would need to clear the cache every time self.headers gets
    # updated in any way...
    @property
    def header_list(self):
        """Get the headers contained in the headers dictionary list as a
        list."""
        headers = []
        for h in self.variables:
            headers.append(h['name'])
        return headers

    def _spawn_field(self, header_info):
        """Add a header field in the next spot with default name & value."""
        if self._row >= self._max_rows:
            self._row = 1
            self._column += 2
            self._add_custom_header_button.grid(row=0,
                                                column=0,
                                                columnspan=self._column*2,
                                                sticky='ew')

        self.variables.append({"name": header_info['name'],
                               "value": None,
                               "enabled": None})

        self._add_entry(-1, row=self._row, column=(self._column + 1),
                        sticky='w', root=self.rightside)
        self._add_box(-1, header_info['name'] + ":", root=self.rightside,
                      row=self._row, column=self._column, sticky='w')

        self._row += 1

    def _add_custom_header(self):
        """Add a custom header box."""
        self.root.grab_set()
        header = simpledialog.askstring("Add Custom Header",
                                        "Enter the header name:",
                                        parent=self.root)
        if header is None:
            return  # user hit cancel
        self.coordinator.headers.add_header(header, "")
        self._spawn_field(self.coordinator.headers.headers[-1])

    def spawn_gui_basics(self):
        """Spawn the base parts of the GUI."""

        self.leftside = tk.LabelFrame(self.root, text="Auto Config",
                                      relief=tk.RIDGE, **self.colors)
        self.rightside = tk.LabelFrame(self.root, text="Headers",
                                       relief=tk.RIDGE, **self.colors)
        self.leftside.grid(row=0, column=0)
        self.rightside.grid(row=0, column=1)

        self.root.wm_title("Edit Headers")
        self.root.config(**self.colors)

        # auto-config left side frame
        self._add_button("Loopback backscatter spam",
                         self.coordinator.callbacks['backscatterEn'],
                         root=self.leftside, row=0, column=0, sticky='ew')

        btn = self._add_button('Add Custom Header', self._add_custom_header,
                               row=0, column=int(self._column / 2),
                               columnspan=2, sticky='ew',
                               root=self.rightside)
        self._add_custom_header_button = btn

        self._add_button("Random Display From",
                         self.coordinator.callbacks['randomDisplayFrom'],
                         root=self.leftside, row=1, column=0, sticky='ew')



        for header in self.coordinator.headers.headers:
            self._spawn_field(header)


class VerificationGUI(GUIBase):
    """This class handles the graphical interface for verifying an
    email is valid and exists."""

    def __init__(self, coordinator):
        """Instantiate the VerificationGUI."""
        super(VerificationGUI, self).__init__(coordinator,
                                              coordinator.gui.root,
                                              'verification')
        self.entry_width = self.entry_width // 3

        with open("validation.regex", 'r') as regex:
            lines = regex.readlines()
        pattern = ''
        for line in lines:
            pattern += line.strip()

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

    def verify_syntax(self):
        """Verify that the email provided is compliant with RFC2822 grammar."""
        self.variables['output_5322'].set('Please wait...')
        if check_rfc_5322(self.coordinator.gui.variables['to'].get()):
            msg = "Email is RFC2822 grammar compliant"
        else:
            msg = "Email is *not* compliant with RFC2822 grammar"

        self.variables['output_5322'].set(msg)

    def verify_using_vrfy(self):
        """Verify an email using SMTP VRFY command."""
        serv = self.coordinator.gui.variables['server'].get()
        self.variables['output_vrfy'].set('Please wait...')
        resp = verify_to(self.coordinator.gui.variables['to'].get(), serv)
        self.root.after(10, self.fin_verify_using_vrfy, resp)

    def fin_verify_using_vrfy(self, resp):
        """Complete the update actions."""
        try:
            resp = resp.resp[0]
        except AttributeError:
            self.root.after(30, self.fin_verify_using_vrfy, resp)
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
        self.root.after(25, self.fin_verify_using_mail, resp)

    def fin_verify_using_mail(self, resp):
        """Complete the update actions."""
        try:
            resp = resp.resp[0]
        except AttributeError:
            self.root.after(75, self.fin_verify_using_mail, resp)
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

        self._add_button("RFC2822", self.verify_syntax,
                         row=4, column=0, sticky='w')
        self._add_changinglabel("", 'output_5322', row=4, column=1, sticky='w')

        self._add_button("SMTP VRFY", self.verify_using_vrfy,
                         row=5, column=0, sticky='w')
        self._add_changinglabel("", 'output_vrfy', row=5, column=1, sticky='w')

        self._add_button("Try emailing", self.verify_using_mail,
                         row=6, column=0, sticky='w')
        self._add_changinglabel("", 'output_email', row=6, column=1,
                                sticky='w')


class EmailEditorGUI(GUIBase):
    """This class is responsible for handling email editing in a blown-up
    window.  It is also capable of adding/removing payloads and attachments.
    """

    def __init__(self, coordinator):
        """Instantiate the editor GUI instance."""
        super(EmailEditorGUI, self).__init__(coordinator,
                                             coordinator.gui.root,
                                             'editor')

        self._active_payload = None
        self.sel_payload = tk.IntVar(0)
        self._pay_sels = []

    def close_action(self):
        """Deregister the GUI with the coordinator."""
        #self.sync_to_main()
        pass

    def sync_from_main(self):
        """Pull the data (message) from the coordinator."""
        self.spawn_payload_selectors()
        self.switch_to_payload()

    def sync_to_main(self):
        """Push data (message) back to coordinator."""
        # 'end-1c' comes from a SO answer
        # credit to Bryan Oakley
        # https://stackoverflow.com/a/14824164/4612410
        self.coordinator.active_guis['main'].variables['text'].set(
            self.editor.get("1.0", "end-1c")
        )
        self.coordinator.active_guis['main'].dump_values_to_coordinator()

    def switch_to_payload(self):
        """Determine which payload the user has selected, and push its contents
        to the editor frame."""

        # first, dump & clear whatever is in the widget
        if self._active_payload is not None:
            self._active_payload._payload = self.editor.get("1.0", "end-1c")
            self.editor.delete("1.0", tk.END)

        # now, insert the new payload
        # indicies of our _pay_sels and the EmailBuilder's internal mimemulti
        # object line up, so we can simply display the payload at the index of
        # our .sel_payload.get() value
        payloads = self.coordinator.email.getmime()._payload
        self._active_payload = payloads[self.sel_payload.get()]
        self.editor.insert(tk.END, self._active_payload._payload)


    def spawn_gui_elements(self):
        """Create the GUI elements necessary."""
        leftframe = tk.LabelFrame(self.root, text="Add Payload",
                                  relief=tk.RIDGE, **self.colors)
        leftframe.grid(row=0, column=0, columnspan=1, sticky='w')

        self.payframes = tk.LabelFrame(self.root, text="Payloads",
                                       relief=tk.RIDGE, **self.colors)
        self.payframes.grid(row=1, column=0, columnspan=1, sticky='w')

        rightframe = tk.Frame(self.root, **self.colors)
        rightframe.grid(row=0, column=1, rowspan=10, columnspan=10,
                        sticky='nesw')

        self.editor = scrolledtext.ScrolledText(rightframe,
                                                wrap=tk.WORD,
                                                width=60,
                                                height=20)
        self.editor.grid(row=0, column=0)

        rp = self._add_button('Random Payload',
                              self.coordinator.callbacks['addRandomPayload'],
                              root=leftframe,
                              row=1, column=0, sticky='ew')
        Tooltip(rp, text="Add lorem ipsum text")

        et = self._add_button('Empty Text',
                              self.coordinator.callbacks['addEmptyPayload'],
                              root=leftframe,
                              row=0, column=0, sticky='ew')
        Tooltip(et, text="Empty text box to add arbitrary text")

        fa = self._add_button("File Attachment",
                              self.coordinator.callbacks['addFilePayload'],
                              root=leftframe,
                              row=2, column=0, sticky='ew')
        Tooltip(fa, text="Generally a bad idea to add files this way!  Use the"
                " attach option in the main window")

    def spawn_payload_selectors(self):
        """Create the GUI elements to select different message payloads."""
        payloads = self.coordinator.email.getmime()._payload

        # first, despawn any old selectors to avoid overwriting problems
        for selector in self._pay_sels:
            selector.destroy()
        self.sel_payload.set(0)

        i = 0
        for payload in payloads:
            sel = tk.Radiobutton(self.payframes, text=str(i),
                                 variable=self.sel_payload,
                                 value=i,
                                 command=self.switch_to_payload,
                                 **self.colors)
            sel.grid(row=i, column=0, sticky='w')
            self._pay_sels.append(sel)
            i += 1



class SMTPResponseCodeLookupGUI(GUIBase):
    """This class is responsible for using looking up SMTP response codes
    in a user-friendly manner."""

    def __init__(self, coordinator):
        """Instantiate the resp. code lookup GUI."""
        super(SMTPResponseCodeLookupGUI, self).__init__(coordinator,
                                                        coordinator.gui.root,
                                                        "codelookup")

        self.codes = self.coordinator.overall_config['SMTP_resp_codes']

    def do_lookup(self):
        """Handle the action for looking up a response code."""
        # TODO: implement this!
        code = self.entryvar.get()
        try:
            message = self.codes[code]
        except KeyError:
            # couldn't find it
            message = "I don't know that response code!"
        self.variables['output'].set(message)

    def spawn_gui(self):
        """Create the window."""

        # TODO: redo this using self._add_combobox now that that exists
        self.entryvar = tk.StringVar()
        self.entry = ttk.Combobox(self.root, textvariable=self.entryvar,
                                  height=len(self.codes), width=8)
        self.entry.grid(row=0, column=0, sticky='w')

        self.entry['values'] = list(self.codes.keys())

        self._add_button("Lookup", callback=self.do_lookup, row=0, column=1,
                         sticky='w')

        self._add_changinglabel(text=" " * 60, varname="output", row=0,
                                column=2, sticky='w')
