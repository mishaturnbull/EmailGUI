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

import smtplib
import platform
import sys

from prereqs import CONFIG, tk, filedialog, ttk, scrolledtext, args, \
                    messagebox, FakeSTDOUT, POPUP_ERRORS, GUI_DOC, \
                    MAX_RESP_LEN, EmailSendError

from helpers import suggest_thread_amt, verify_to, verify_to_email

from uibase import EmailPrompt

CONFIG['multithread'] = suggest_thread_amt(int(CONFIG['amount']))


class EmailerGUI(EmailPrompt):
    '''Make things easier to use, and prettier.'''

    colors = {"background": CONFIG['colors']['bg'],
              }
    buttons = {"background": CONFIG['colors']['buttons'],
               "activebackground": CONFIG['colors']['bg'],
               }

    def __init__(self):
        '''Start the class, and make stuff happen.'''
        EmailPrompt.__init__(self, _autorun=False)
        self.root = tk.Tk()

        self._gui_elem = {}

        self.init_gui()

        self._display_from_prev = ""

        self.root.protocol('WM_DELETE_WINDOW', self.exit)

        # self.root.mainloop needs to be called sometimes - but not always?
        # can't figure out a pattern here.
        if platform.system() in ['Linux', 'Darwin']:
            self.root.mainloop()
        if sys.version_info.major == 3 and platform.system() == 'Windows':
            self.root.mainloop()

    # stolen from the `sender.py` file -- allows us to keep down the
    # massive number of attributes that are normally
    # associated with a GUI to 1 (large) dictionary

    def __setitem__(self, key, value):
        self._gui_elem[key] = value

    def __contains__(self, key):
        return key in self._gui_elem

    def __getitem__(self, key):
        return self._gui_elem[key]

    def exit(self):
        '''Close the window. '''
        self.root.destroy()

    def handler_button_send(self):
        '''Handle the 'Send' button being clicked.
           Tries to send the message, but if it doesn't work spawns a
           popup saying why.'''

        # ask for confirmation
        if messagebox.askyesno(CONFIG['title'],
                               ' '.join(CONFIG['confirmation_msg'])):
            try:
                self.create_msg_config()
                # dear reader, you might be inclined to expect something like:
                # for i in BEST_RANGE(len(self.frm)):
                #    self.send_msg()
                # but this is not what you see.  instead, we just let
                # EmailPromp's .send_msg() handle the looping -- if we do it
                # here as well, the program sends exactly twice as many emails
                # as it should because it sends emails i times, i times.
                # therefore shouldn't loop here.
                self.send_msg(self)
            except smtplib.SMTPResponseException as exc:
                if isinstance(exc, tuple(POPUP_ERRORS)):
                    messagebox.showerror(CONFIG['title'], exc.smtp_error)
            except smtplib.SMTPException as exc:
                if isinstance(exc, tuple(POPUP_ERRORS)):
                    messagebox.showerror(CONFIG['title'], exc.args[0])

    def handler_button_abort(self):
        '''Do our best job at stopping the sending of further emails.'''

        # reset mode
        if self._sender.is_done:
            self['bar_progress']["value"] = 0
            self['label_progress'].config(text="Sent: 0 / 0")

            self._all_senders = []
            self._sender = None

            # switch back to abort
            self['button_abort']["text"] = "Abort"

        # abort mode
        else:
            for sender in self._all_senders:
                sender.abort()

    def handler_automt(self):
        '''Handle the 'Auto-select Threading' button.
           Checks with the function suggest_thread_amt() using the specified
           number of emails, then sets multithreading mode accordingly.'''

        suggestion = suggest_thread_amt(int(self['entry_amount'].get()))
        self.query_multithreading.set(suggestion[0])  # set the mode
        self['query_conmode'].set(suggestion[2])

        # if limited, set num. threads
        if suggestion[0] == 'lim':
            self['n_threads'].delete(0, 'end')  # clear field
            self['n_threads'].insert(0, str(suggestion[1]))

        # if no multithreading, set delay
        elif suggestion[0] == 'none':
            self['entry_delay'].delete(0, 'end')  # clear field
            self['entry_delay'].insert(0, str(suggestion[1]))

    def handle_forge_from(self):
        '''Handle the 'Display from' checkbox state-change.'''

        is_forging = bool(self.forge_from.get())

        if CONFIG['debug']:
            print("Handling forge from mode change to {}".format(
                is_forging))

        if is_forging:
            self['entry_df'].config(state='normal')
            self['backscatter_box'].config(state='normal')
        else:
            self['entry_df'].config(state='disabled')
            self['backscatter_box'].config(state='disabled')

    def handler_backscatter(self):
        '''Handle the 'Increase Backscatter' checkbox state-change.'''
        is_backscattering = bool(self.increase_backscatter.get())

        if CONFIG['debug']:
            print("Handling backscatter mode change to {}".format(
                is_backscattering))

        if is_backscattering:
            self._display_from_prev = self.display_from_content.get()
            self['entry_df'].config(textvariable=self.recipient_addresses,
                                    state='disabled')
        else:
            self.display_from_content.set(self._display_from_prev)
            self['entry_df'].config(textvariable=self.display_from_content,
                                    state='normal')

    def create_msg_config(self):
        '''Create the necessary attributes to create a message.
           Raises EmailSendError if something important is missing.'''
        self.server = self['entry_server'].get()
        self.frm = self['entry_from'].get()
        self.display_from = self.display_from_content.get()
        self.password = self['entry_password'].get() or args.PASSWORD
        self.text = self['entry_text'].get()
        self.subject = self['entry_subject'].get()
        self.amount = int(self['entry_amount'].get())
        self.rcpt = self.recipient_addresses.get()
        mt_mode = self.query_multithreading.get()
        mt_num = int(self['n_threads'].get())
        conmode = self.query_conmode.get()
        self.multithreading = (mt_mode, mt_num, conmode)
        self.files = self['entry_file'].get().split(',')
        delay = self['entry_delay'].get()
        if delay == '':
            self.delay = 0
        else:
            self.delay = delay
        if self.files == ['']:
            self.files = []

        # Pylint yells about this.
        # It doesn't like that we redefine CONFIG['max_retries'] inside
        # something, and it doesn't see it being used in this method.
        # It is right about both, so I didn't silence it, BUT:
        # Yeah, redefining names is bad but the value isn't changed by the
        # program, only the user.
        # It's not used in this method, but is used later in the program
        # and its value can make a difference in execution.
        CONFIG['max_retries'] = int(self['entry_retry'].get())
        if not all([bool(x) for x in [self.server, self.frm, self.text,
                                      self.subject, self.amount, self.rcpt]]):
            raise EmailSendError("One or more required fields left blank!")
        self.split_accounts()  # split server, frm, password into lists

    def split_accounts(self):
        '''Take the user-given values for .frm, .password and .server
        and split them on commas (and strip whitespace).  If the lists are of
        unequal length, sort that out too.'''
        self.server = [a.strip() for a in self.server.split(',')]
        self.frm = [a.strip() for a in self.frm.split(',')]
        self.password = [a.strip() for a in self.password.split(',')]

        # we want the lists to have the same length as self.frm -- the user
        # could have 2 or more accounts with the same address and server
        # this way, we assume if less passwords and/or servers are given
        # that we populate the rest of the lists with clones of the last
        # element
        if len(self.server) < len(self.frm):
            self.server += [self.server[-1]] * (len(self.frm) -
                                                len(self.server))
        if len(self.password) < len(self.frm):
            self.password += [self.password[-1]] * (len(self.frm) -
                                                    len(self.password))

    def _make_sender(self, i=0, bar_update_handler=None):
        self.create_msg_config()
        EmailPrompt._make_sender(self, i, bar_update_handler)

    def check_retcode(self):
        '''Look up an SMTP return error code and get its message.'''
        def lookup_code():
            '''Do the dirty work of setting the message to what it should
            be.'''
            retcode = int(entry_resp.get())
            if retcode not in CONFIG['SMTP_resp_codes']:
                msg = "Sorry, I don't know that one!" + (" " * (MAX_RESP_LEN -
                                                                29))
            else:
                msg = CONFIG['SMTP_resp_codes'][retcode]
                msg += (" " * (MAX_RESP_LEN - len(msg)))
            label_code.config(text=msg)

        retmen = tk.Toplevel(self.root)
        retmen.wm_title("Response codes")
        retmen.config(**self.colors)
        label_resp = tk.Label(retmen, text="Response code: ", **self.colors)
        label_resp.grid(row=0, column=0, sticky=tk.W)
        entry_resp = tk.Entry(retmen, width=4)
        entry_resp.grid(row=0, column=1, sticky=tk.W)
        label_err = tk.Label(retmen, text="Error: ", **self.colors)
        label_err.grid(row=1, column=0, sticky=tk.W)
        label_code = tk.Label(retmen, text=(' ' * 62), **self.colors)
        label_code.grid(row=1, column=1, sticky=tk.W)
        button_lookup = tk.Button(retmen, text='Look up', command=lookup_code,
                                  **self.buttons)
        button_lookup.grid(row=3, column=0, sticky=tk.W)

    def handler_button_help(self):
        """Display program documentation."""
        helper = tk.Toplevel(self.root)
        helper.title("Help")
        txt = scrolledtext.ScrolledText(helper)
        txt.insert(tk.END, GUI_DOC)
        txt['font'] = ('liberation mono', '10')
        txt.pack(expand=True, fill='both')

    def verify_to(self):
        """Verify the email address the user wants to send to and show
        a message box containing the result.  Graphical mode only."""
        def vrfy():
            '''Button handler for verify mode using SMTP vrfy verb.'''
            serv = self['entry_server'].get() or CONFIG['server']
            label_vrfy_res.config(text=' ')
            resp = verify_to(entry_to.get(), serv)
            resp = resp[0]
            if resp == 250:
                msg = str(resp) + " Email appears valid."
            elif resp == 251:
                msg = str(resp) + " Email appears forwarded."
            elif resp == 252:
                msg = str(resp) + " Server could not determine."
            else:
                msg = str(resp) + "Address either invalid or unable to determine."
            label_vrfy_res.config(text=msg)

        def mail():
            '''Button handler for verify mode using email test.'''
            serv = self['entry_server'].get() or CONFIG['server']
            label_mail_res.config(text=' ')
            resp = verify_to_email(entry_to.get(),
                                   serv,
                                   entry_from.get(),
                                   entry_password.get())
            resp = resp[0]
            if resp == 550:
                msg = str(resp) + " Email appears invalid."
            elif resp == 250:
                msg = str(resp) + " Email appears valid."
            else:
                msg = str(resp) + " Could not determine."
            label_mail_res.config(text=msg)

        def paste_addr():
            '''Button handler for paste address into main window.'''
            self['entry_to'].delete(0, len(self['entry_to'].get()))
            self['entry_to'].insert(0, entry_to.get())

        def paste_serv():
            '''Button handler for paste server into main window.'''
            self['entry_server'].delete(0, len(self['entry_server'].get()))
            self['entry_server'].insert(0, entry_serv.get())

        vrfymen = tk.Toplevel(self.root)
        vrfymen.config(**self.colors)
        vrfymen.wm_title("Verification")
        label_from = tk.Label(vrfymen, text='Verify from:', **self.colors)
        label_from.grid(row=0, column=0, sticky=tk.W)
        entry_from = tk.Entry(vrfymen, width=40)
        entry_from.grid(row=0, column=1, columnspan=2, sticky=tk.W)
        entry_from.insert(0, self['entry_from'].get().split(',')[0])
        label_password = tk.Label(vrfymen, text='Verify password:',
                                  **self.colors)
        label_password.grid(row=1, column=0, sticky=tk.W)
        entry_password = tk.Entry(vrfymen, width=40, show='*')
        entry_password.grid(row=1, column=1, columnspan=2, sticky=tk.W)
        entry_password.insert(0, self['entry_password'].get())
        label_to = tk.Label(vrfymen, text='To:', **self.colors)
        label_to.grid(row=2, column=0, sticky=tk.W)
        entry_to = tk.Entry(vrfymen, width=40)
        entry_to.grid(row=2, column=1, columnspan=2, sticky=tk.W)
        entry_to.insert(0, self['entry_to'].get())
        label_serv = tk.Label(vrfymen, text="Server:", **self.colors)
        label_serv.grid(row=3, column=0, sticky=tk.W)
        entry_serv = tk.Entry(vrfymen, width=40)
        entry_serv.grid(row=3, column=1, columnspan=2, sticky=tk.W)
        entry_serv.insert(0, self['entry_server'].get())
        button_vrfy = tk.Button(vrfymen, text="vrfy", command=vrfy,
                                **self.buttons)
        button_vrfy.grid(row=4, column=0, sticky=tk.W)
        label_vrfy_res = tk.Label(vrfymen, text="", **self.colors)
        label_vrfy_res.grid(row=4, column=1, sticky=tk.W)
        button_mail = tk.Button(vrfymen, text="mail", command=mail,
                                **self.buttons)
        button_mail.grid(row=5, column=0, sticky=tk.W)
        label_mail_res = tk.Label(vrfymen, text="", **self.colors)
        label_mail_res.grid(row=5, column=1, sticky=tk.W)
        button_paste_addr = tk.Button(vrfymen, text="Paste address",
                                      command=paste_addr,
                                      **self.buttons)
        button_paste_addr.grid(row=6, column=0, sticky=tk.W)
        button_paste_serv = tk.Button(vrfymen, text="Paste server",
                                      command=paste_serv,
                                      **self.buttons)
        button_paste_serv.grid(row=6, column=1, sticky=tk.W)

    def init_gui(self):
        '''Build that ugly GUI.'''
        # ws = int(self.root.winfo_screenwidth() / 2)
        # hs = int(self.root.winfo_screenheight() / 2)
        self.root.title(CONFIG['title'])
        self.root.config(background=CONFIG['colors']['bg'])

        # if the length of CONFIG['text'] is greather than 100, use 100 as the
        # limit of the window width.  prevents window being wider than the
        # screen on smaller screens (laptops)
        width = CONFIG["width"]

        # number to send
        self['label_amount'] = tk.Label(self.root, text='# emails: ',
                                        **self.colors)
        self['label_amount'].grid(row=1, column=0, sticky=tk.W)
        self['entry_amount'] = tk.Entry(self.root, width=5)
        self['entry_amount'].grid(row=1, column=1, sticky=tk.W)
        self['entry_amount'].insert(0, CONFIG['amount'])

        # subject
        self['label_subject'] = tk.Label(self.root, text='Subject: ',
                                         **self.colors)
        self['label_subject'].grid(row=2, column=0, sticky=tk.W)
        self['entry_subject'] = tk.Entry(self.root, width=width)
        self['entry_subject'].grid(row=2, column=1, columnspan=9,
                                   sticky=tk.W + tk.E)
        self['entry_subject'].insert(0, CONFIG['subject'])

        # text
        self['label_text'] = tk.Label(self.root, text='Message text: ',
                                      **self.colors)
        self['label_text'].grid(row=7, column=0, sticky=tk.W)
        self['entry_text'] = tk.Entry(self.root, width=width)
        self['entry_text'].grid(row=7, column=1, columnspan=9,
                                sticky=tk.W + tk.E)
        self['entry_text'].insert(0, CONFIG['text'])

        # from
        self['label_from'] = tk.Label(self.root, text='From | display as: ',
                                      **self.colors)
        self['label_from'].grid(row=3, column=0, sticky=tk.W)
        self['entry_from'] = tk.Entry(self.root, width=int(width/3 * 2))
        self['entry_from'].grid(row=3, column=1, columnspan=6,
                                sticky=tk.W + tk.E)
        self['entry_from'].insert(0, CONFIG['from'])

        # display from
        # XXX: soon to be moved to a separate display window for header tags
        self.display_from_content = tk.StringVar()
        self.display_from_content.set(CONFIG['display_from'])
        self['entry_df'] = tk.Entry(self.root, width=int(width/3),
                                    textvariable=self.display_from_content)
        self['entry_df'].grid(row=3, column=7, columnspan=3,
                              sticky=tk.W + tk.E)

        # from password
        self['label_password'] = tk.Label(self.root, text='Password: ',
                                          **self.colors)
        self['label_password'].grid(row=4, column=0, sticky=tk.W)
        self['entry_password'] = tk.Entry(self.root, show='*',
                                          width=width)
        self['entry_password'].grid(row=4, column=1, columnspan=9,
                                    sticky=tk.W + tk.E)
        # only allow default passwords if the user specified one
        # otherwise set it to none
        self['entry_password'].insert(0, args.PASSWORD or '')

        # to
        self['label_to'] = tk.Label(self.root, text='To: ',
                                    **self.colors)
        self['label_to'].grid(row=5, column=0, sticky=tk.W)
        self.recipient_addresses = tk.StringVar()
        self.recipient_addresses.set(CONFIG['to'])
        self['entry_to'] = tk.Entry(self.root, width=width,
                                    textvariable=self.recipient_addresses)
        self['entry_to'].grid(row=5, column=2, columnspan=8)

        # check email
        self['button_vrfy'] = tk.Button(self.root, text='Verify',
                                        command=self.verify_to,
                                        **self.buttons)
        self['button_vrfy'].grid(row=5, column=1)

        # server
        self['label_server'] = tk.Label(self.root, text='Server: ',
                                        **self.colors)
        self['label_server'].grid(row=6, column=0, sticky=tk.W)
        self['entry_server'] = tk.Entry(self.root, width=width)
        self['entry_server'].grid(row=6, column=1, columnspan=9,
                                  sticky=tk.W + tk.E)
        self['entry_server'].insert(0, CONFIG['server'])

        # progress bar!
        self['label_progress'] = tk.Label(self.root, text="Sent: 0 / 0 ",
                                          **self.colors)
        self['label_progress'].grid(row=9, column=0, sticky=tk.W)
        self['bar_progress'] = ttk.Progressbar(self.root, orient='horizontal',
                                               length=600, mode='determinate')
        self['bar_progress'].grid(row=9, column=2, columnspan=8)

        # abort button
        self['button_abort'] = tk.Button(self.root, text="Abort",
                                         command=self.handler_button_abort,
                                         **self.buttons)
        self['button_abort'].grid(row=9, column=1, sticky=tk.W)

        # multithreading
        self['label_multithread'] = tk.Label(self.root,
                                             text='Multithreading mode:',
                                             **self.colors)
        self['label_multithread'].grid(row=10, column=0, sticky=tk.W)
        self.query_multithreading = tk.StringVar()
        self.query_multithreading.set(CONFIG['multithread'][0])
        self['mt_none'] = tk.Radiobutton(self.root, text='None',
                                         variable=self.query_multithreading,
                                         value='none',
                                         **self.colors)
        self['mt_lim'] = tk.Radiobutton(self.root, text='Limited: ',
                                        variable=self.query_multithreading,
                                        value='lim',
                                        **self.colors)
        self['mt_ulim'] = tk.Radiobutton(self.root, text='Unlimited',
                                         variable=self.query_multithreading,
                                         value='ulim',
                                         **self.colors)
        self['mt_none'].grid(row=11, column=0, sticky=tk.W)
        self['mt_lim'].grid(row=12, column=0, sticky=tk.W)
        self['mt_ulim'].grid(row=13, column=0, sticky=tk.W)
        self['n_threads'] = tk.Entry(self.root, width=3)
        self['n_threads'].insert(0, CONFIG['multithread'][1])
        self['n_threads'].grid(row=12, column=1, sticky=tk.W)

        self['entry_delay'] = tk.Entry(self.root, width=3)
        self['entry_delay'].grid(row=11, column=1, sticky=tk.W)
        self['entry_delay'].insert(0, CONFIG['delay'])

        # file attachments
        self['label_file'] = tk.Label(self.root, text='Attachments: ',
                                      **self.colors)
        self['label_file'].grid(row=8, column=0, sticky=tk.W)
        self['entry_file'] = tk.Entry(self.root, width=width)
        self['entry_file'].grid(row=8, column=2, columnspan=8)
        self['entry_file'].insert(0, CONFIG['attach'])
        # server options label
        self['opt_label1'] = tk.Label(self.root, text='Server options:',
                                      **self.colors)
        self['opt_label1'].grid(row=10, column=2, sticky=tk.W)

        # max server retry attempts
        self['label_retry'] = tk.Label(self.root, text='Max. Retries: ',
                                       **self.colors)
        self['label_retry'].grid(row=11, column=2, sticky=tk.W)
        self['entry_retry'] = tk.Entry(self.root, width=3)
        self['entry_retry'].insert(0, str(CONFIG['max_retries']))
        self['entry_retry'].grid(row=11, column=3, sticky=tk.W)

        # connect once or per email
        self.query_conmode = tk.BooleanVar()
        self.query_conmode.set(False)
        self['con_once'] = tk.Radiobutton(self.root, text='Connect once',
                                          variable=self.query_conmode,
                                          value=False,
                                          **self.colors)
        self['con_per'] = tk.Radiobutton(self.root, text='Connect per send',
                                         variable=self.query_conmode,
                                         value=True,
                                         **self.colors)
        self['con_once'].grid(row=12, column=2, sticky=tk.W)
        self['con_per'].grid(row=13, column=2, sticky=tk.W)

        # compliance options
        self['label_compliance'] = tk.Label(self.root,
                                            text="RFC2822 Compliance",
                                            **self.colors)
        self['label_compliance'].grid(row=10, column=4, sticky=tk.W)

        self.forge_from = tk.IntVar()
        self.forge_from.set(1)
        self['forge_from_box'] = tk.Checkbutton(self.root, text="Forge sender",
                                                variable=self.forge_from,
                                                command=self.handle_forge_from,
                                                **self.colors)
        self['forge_from_box'].grid(row=11, column=4, sticky=tk.W)

        # backscatter spam mode
        self.increase_backscatter = tk.IntVar()
        self.increase_backscatter.set(0)
        self['backscatter_box'] = \
            tk.Checkbutton(self.root,
                           text="Increase backscatter",
                           variable=self.increase_backscatter,
                           command=self.handler_backscatter,
                           **self.colors)
        self['backscatter_box'].grid(row=12, column=4, sticky=tk.W)

        def browse_file():
            '''Helper to display a file picker and insert the result in the
            file_entry field.'''
            filename = filedialog.askopenfilename()
            if self['entry_file'].get() != '':
                self['entry_file'].insert(0, filename + ",")
            else:
                self['entry_file'].delete(0, 'end')
                self['entry_file'].insert(0, filename)

        self['button_filebrowse'] = tk.Button(self.root, text='Browse',
                                              command=browse_file,
                                              **self.buttons)
        self['button_filebrowse'].grid(row=8, column=1)

        # Options
        self.menu_top = tk.Menu(self.root)
        self.menu_email = tk.Menu(self.menu_top, tearoff=0)
        self.menu_email.add_command(label='Send',
                                    command=self.handler_button_send)
        self.menu_email.add_command(label='Auto-Select Threading',
                                    command=self.handler_automt)
        self.menu_top.add_cascade(label='Email', menu=self.menu_email)

        self.menu_clientside = tk.Menu(self.menu_top, tearoff=0)
        self.menu_clientside.add_command(label='Exit', command=self.exit)
        self.menu_top.add_cascade(label='Client', menu=self.menu_clientside)

        self.menu_help = tk.Menu(self.menu_top, tearoff=0)
        self.menu_help.add_command(label='Documentation',
                                   command=self.handler_button_help)
        self.menu_help.add_command(label='SMTP Response code lookup',
                                   command=self.check_retcode)
        self.menu_top.add_cascade(label='Help', menu=self.menu_help)

        self.root.config(menu=self.menu_top)

        # label CONFIG['debug'] mode if it is on
        if CONFIG['debug']:
            label_debug = tk.Label(self.root, text='DEBUG MODE ACTIVE')
            label_debug.grid(row=1, column=2)


# %% main
if __name__ == '__main__':
    try:
        sys.stdout = FakeSTDOUT(sys.stdout, CONFIG['log_stdout'])
        sys.stderr = FakeSTDOUT(sys.stderr, CONFIG['log_stderr'])
        # DO STUFF!
        if not args.NOGUI:
            EmailerGUI()
        elif args.NOGUI:
            EmailPrompt()
        elif args.COMMANDLINE:
            gui = EmailPrompt(_autorun=False)
            gui.send_msg()
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout = sys.stdout.FSO_close()
        sys.stderr = sys.stderr.FSO_close()
