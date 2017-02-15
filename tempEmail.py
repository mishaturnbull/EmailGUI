
# -*- coding: utf-8 -*-
import smtplib
from threading import current_thread
import sys
ident = sys.argv[1]

serveraddress = 'smtp.gmail.com:587'
From = 'michael.turnbull@stjlabs.com'
to = 'michael.turnbull@stjlabs.com'
password = 'Febfd3323374973'
message = \
'''Content-Type: multipart/mixed; boundary="===============7005917460624756678=="
MIME-Version: 1.0
reply-to: fake@fake.com
From: "fake@fake.com" <fake@fake.com>
X-Google-Originally-From: "fake@fake.com" <fake@fake.com>
To: michael.turnbull@stjlabs.com
Date: Tue, 14 Feb 2017 13:52:33 -0500
Subject: Apology

--===============7005917460624756678==
Content-Type: text/plain; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit

Dear recipient,
I am writing to apologize for incessantly writing you emails.  It must be
tiresome to spend all day deleting them.


P.S. Please forgive me for sending this email.  I shall immediately dispatch
a second email in apology.

Email from {ident} on ulim
--===============7005917460624756678==--

'''.format(thread=current_thread(), ident=ident)

server = smtplib.SMTP(serveraddress)
server.set_debuglevel(1)
server.ehlo_or_helo_if_needed()
server.starttls()
server.ehlo()
# not as worried about 421 disconnects here -- it would only affect one email
server.login(From, password)
server.sendmail(From, to, message)
server.quit()
