# -*- coding: utf-8 -*-
"""
Contains 'simpler' helper functions that don't depend on other functionality.
"""

import smtplib
import ipaddress
import math
import re
import time

from prereqs import VALIDATION_RE


def time_from_epoch(sec, tzconvert=True):
    tstruct = time.gmtime(sec)
    if tzconvert:
        hr = tstruct.tm_hour - 5
    else:
        hr = tstruct.tm_hour
    mn = tstruct.tm_min
    sec = tstruct.tm_sec
    out = "{0:02d}:{1:02d}:{2:02d}".format(hr, mn, sec)
    return out


def suggest_thread_amt(coordinator):
    '''Given the current settings input by the user, determine the
    best settings for the more advanced tweakables.'''
    amount = coordinator.settings['amount']
    server = coordinator.settings['server'].split(':')[0]
    localp = ipaddress.ip_address(server).is_private
    recommend = {"mt_mode": 'none',
                 "mt_num": 0,
                 "delay": 0,
                 "con_mode": 'con_once',
                 "con_num": 0,
                 "max_retries": 5}

    if localp:
        # distribute the work equally among threads as much as possible
        # easiest to do by square-rooting the value
        recommend['mt_mode'] = 'limited'
        recommend['mt_num'] = int(math.sqrt(amount))
    else:
        # now we have some thinking to do.  most mail servers don't allow
        # more than 15 threads, so whatever we do we should maximize
        # threads up to that point
        if amount <= 15:
            recommend['mt_mode'] = 'unlimited'
        elif amount < 500:
            recommend['mt_mode'] = 'limited'
            recommend['mt_num'] = 15
        else:
            # at this point, worry about dealing with, for example,
            # Gmail's limit of 500emails/24hour.  Deal with this by simply
            # reducing the rate of total sending to a rate that fits that --
            # approximately 1 email every 180 seconds (3min)
            recommend['mt_mode'] = 'none'
            recommend['delay'] = 180
            recommend['con_mode'] = 'con_per'

    if 500 > amount >= 100:
        # good idea to reconnect every so often just to make sure that
        # they're still going through
        recommend['con_mode'] = 'con_some'
        recommend['con_num'] = 100

    assert not all(recommend.values()), \
        "did not successfully make a recommendation"

    return recommend


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


def check_rfc_5322(address):
    """Given a string representing an email address, determine whether or not
    it is compliant with the RFC 5322 grammar specification."""
    # turns out that the RFC 5322 grammar spec is quite complex
    # thanks to this S.O. answer where I got the regex snippet from
    # https://stackoverflow.com/a/201378/4612410
    # credit to user bortzmeyer & community wiki
    regex = re.compile(VALIDATION_RE)
    success = regex.search(address)
    return success is not None
