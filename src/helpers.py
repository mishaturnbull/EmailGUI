# -*- coding: utf-8 -*-
"""
Contains 'simpler' helper functions that don't depend on other functionality.
"""

import smtplib

def suggest_thread_amt(coordinator):
    '''Given a total number of emails to send `num_emails`, determine which
multithreading mode/settings would likely be the fastest and least likely to
fail.

Prioritizes likeliehood of success over speed.

Returns a tuple (mt_mode, mt_num, con_per):
    :str: mt_mode := one of ['none', 'lim', 'ulim']
    :int: mt_num := if mt_mode == 'none': one of [0, 180]
                    if mt_mode == 'lim': in range(1, 16)
                    if mt_mode == 'ulim': 0
    :bool: con_per := whether or not a connection should be established
                      for each email

Note that in the case mt_mode == 'none', mt_num actually does not indicate
the number of threads to use, but rather a delay factor for intentionally
slowing down the sending of emails.  This is done to prevent daily send
quota limits from kicking in (for example, Gmail only allows 500 emails to be
send in 24 hours.  Sending one email every 3 minutes (180 seconds) will prevent
emails being blocked by sending less than 500 emails in 24 hours).  However,
it's often more convient to shoot off 500 emails quickly then wait for tomorrow
so instead, for num_emails = 500, return ('none', 0).  Only for num_emails>500
will we return 180.
'''

    # gmail only allows 15 connections to be open at a time from one IP
    # address before it throws a 421 error.  this function should
    # never return a combination which would allow more than 15 active
    # connections to the server.

    num_emails = coordinator.settings['amount']

    if num_emails == 1:
        # just one email.  seriously, why use multithreading??
        out = ('none', 0, 'con_once')

    elif num_emails <= 15:
        # only use unlimited if it won't throw 421 errors -- happens above 15
        out = ('ulim', 0, 'con_once')

    elif 500 > num_emails > 15:
        # limited is our best bet here
        if (num_emails % 15) == 0:
            # the number of emails divides evenly by 15 - use 15 threads and
            # each one gets num_emails / 15 emails to send
            out = ('lim', 15, 'con_once')
        else:
            # num_emails does not divide by 15.  trying to use 15 threads will
            # result in each one having a float value of emails to send, which
            # makes no sense:
            #
            # client: "I want to send 3.3 emails to Joe!"
            # server: "Wut"
            #
            # To avoid this, use 14 threads with the same amount and send
            # the remainder in a 15th
            out = ('lim', 14, 'con_once')
    elif num_emails == 500:
        # send 500 emails, but send them in one shot -- often easier, as noted
        # in the docstring, to send 500 then wait for tomorrow
        out = ('lim', 14, 'con_once')
    elif num_emails > 500:
        # gmail allows no more than 500 emails in 24 hours
        # by using a delay of 2.88 minutes (172.8 seconds), we can send 500
        # emails in exactly 24 hours, thereby never triggering gmail's
        # send quota limit
        #
        # we use 3 minutes (180 seconds) just to be sure that we don't trigger
        # anti-spam
        out = ('none', 180, 'con_per')
    
    return out


def verify_to(address, serv):
    """Given an address and a server to use, send an SMTP VRFY command
    and return the result."""
    # import smtplib
    server = smtplib.SMTP(serv)
    resp = server.verify(address)
    server.quit()
    return resp


def verify_to_email(address, serv, frm, pwd):
    """Given an address and a server to use, attempt to verify the address
    by sending mail to it."""
    # import smtplib
    server = smtplib.SMTP(serv)
    server.ehlo_or_helo_if_needed()
    if server.has_extn("STARTTLS"):
        server.starttls()
        server.ehlo()
    if server.has_extn("AUTH"):
        server.login(frm, pwd)
    server.mail(frm)
    resp = server.rcpt(address)
    server.quit()
    return resp
