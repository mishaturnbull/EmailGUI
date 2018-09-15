[Back to main page](index.html)

# Table of Contents

1.0 [The Layout](#the-layout)

2.0 [Basic configuration](#basic-configuration)  
    2.1 [Number to Send](#number-to-send)  
    2.2 [Subject Line](#subject-line)  
    2.3 [Sending Accounts](#from-accounts)  
        2.3.1 [Sending Addresses](#from-addresses)  
        2.3.2 [Sending Passwords](#from-passwords)  
        2.3.3 [Display From Address](#forge-from-account)  
    2.4 [Recipients](#recipients)  
        2.4.1 [Recipient Address](#recipient-address)  
        2.4.2 [Verify Recipient Address](#verify-button)  
    2.5 [Server](#server)  
    2.6 [Message text](#message)  
    2.7 [Attachments](#attachments)  
        2.7.1 [Browse button](#the-browse-button)  
    2.8 [Progress indicator](#status-indicator)  

3.0 [Advanced configuration](#advanced-configuration)  
    3.1 [Multithreading controls](#multithreading)  
        3.1.1 [MT-NONE](#no-multithreading-mt-none)  
        3.1.2 [MT-LIM](#limited-multithreading-mt-lim)  
        3.1.3 [MT-ULIM](#unlimited-multithreading-mt-ulim)  
    3.2 [Connection controls](#connection-controls)
        3.2.1 [Number of retries](#max-retries)
        3.2.2 [Connect once](#connect-once)
        3.2.3 [Connect per send](#connect-per-send)

# The Layout

<div style="text-align:center">
    <!-- sorry about this if you're reading this file as text or offline... -->
    <img src="https://github.com/mishaturnbull/EmailGUI/raw/master/docs/screencap-1.png"/>
</div>

Let's go over all the fields quickly, with links to their detailed sections for each.  Starting from the top:

[2.1 Number of emails](#number-to-send): How many emails to send, from each account given.  
[2.2 Subject](#subject-line): The subject line of each email.  
[2.3.1 From Address(es)](#from-accounts): The account, or accounts, to send [a given quantity](#number-to-send) of emails from.  
[2.3.3 Display From](#forge-from-account): The address that the email should appear to come from.  
[2.3.2 Password](#from-passwords): The passwords to the accounts that are sending email.  
[2.4.2 To Address](#recipient-address): The address to send emails to  
[2.5 Server](#server): The SMTP server to connect to.  
[2.6 Message](#message): The message text of the email.  
[2.7 Attachments](#attachments): Files to attach to the email, if any.  
[2.8 Progress bar & abort/reset button](#status-indicator): A progress bar and button that helps remedy potential situations.  
[3.0 Advanced connection & threading controls](#advanced-configuration): Advanced options.  Can be configured for you automatically by going to `Email` -> `Auto-Select Threading`  

# Basic Configuration

This section goes over all the text entry fields needed to successfully send emails and edit them past the defaults.

## Number to send

Should be pretty straightforward.  Type in a number, and the person gets that many emails.

Note that if you're sending from multiple addresses ([see section 2.3](#from-accounts)), then this is the number of emails that will be sent *from each account*.

## Subject line

Help docs for a subject line?  Have you used email before?

## Sending accounts

This is where stuff starts to get more interesting.  This program is capable of sending emails from more than one account.  Ironically, this is exactly the opposite of what most mass-mailers do:

```
email1@gmail.com   -----\
email2@gmail.com   -----|
email3@gmail.com   -----+--> recipient@myserver.com
email4@gmail.com   -----|
email5@gmail.com   -----/
```

Of course, you can also just use 1 email account to send from.  I'd recommend using 1 if you're sending using the same server that's receiving, but if you have to go across the internet at all (as opposed to remaining on local intranet, or even better the same machine) then using multiple accounts may be a better idea.

### From addresses

Put the email acounts to send mail from in this line.  If you want to use more than one, separate them with commas.  Whitespace is automatically removed and should not be a factor.

### From passwords

This is where the password goes to the email address you're sending from.  If you have more than 1 account, you can enter the same number of passwords, comma-separated.  If you have multiple accounts dedicated for stressing email servers (like I do) and they all have the same password (bad!  don't do that!), you can simply enter that password once and the program will automatically fill in the rest.

### Forge from account

What could be more fun than emailing your sysadmin as your sysadmin?  Nothing!  The field to the right of the from address entry allows you to enter text that will be replaced in all relevant from tags.  This will get you as close as possible to sending mail as the account you enter there.

***THIS CAN BE USED TO DO BAD AND/OR ILLEGAL THINGS.  IF YOU DO BAD THINGS, I DO NOT CLAIM ANY RESPONSIBILITY FOR YOUR ACTIONS.***

## Recipients

You put email addresses here and then you owe their owner a bottle of whatever they drink, for the headache you're going to cause them.

### Recipient Address

If you want to send to more than one address, separate the victi...er, recipient addresses with commas.  Otherwise, just enter the address that you're sending emails to.

### Verify button

This was implemented to catch typos in addresses and therefore reduce or nullify accidental backscatter spam.  It pulls data automatically from previously populated fields including to, from, password, and server and offers two methods to check whether or not the recipient address is valid.  The first is `SMTP VRFY`.  The "verify" command, enabled on some servers, allows a user to simply check whether or not the address is valid.  The second method is called `MAIL`.  This was implemented on my discovery that there are actually quite few servers that allow a `VRFY` command to be used.  The `MAIL` method simply tries to send them an email and sees if the server rejects it.  It's more reliable, but slower.

Once you find the correct address and server, you can use the `Paste address` and `Paste server` buttons to automatically copy the to address and server into the main window.

## Server

This is the address of the SMTP server you'd like to send email to.  I've listed some common options below (the ones I've used):

| Server          | Address            |
| --------------- | ------------------ |
| Gmail           | smtp.gmail.com:589 |
| Local (Mercury) | 127.0.0.1:25       |

Syntax must be in the form of `<valid URL>:<valid port number>`.

## Message

This is where the text goes.  I think my default is quite funny, but if you have something you want to say, it goes here.

## Attachments

Should you want to attach files or images to your emails, put the location of the file in this entry box.

### The browse button

A `Browse` button has been included for easy file selection.  It opens a file browser for the native OS, and when you select a file, pastes the location into the box automatically.

## Status Indicator

It's a progress bar, Einstein.  

### The Reset Button

This button next to the progress bar does a few things.  First, while sending emails, if clicked before all emails are sent then it aborts sending.

***ABORTING IS DIFFERENT FROM UNDOING***.  Aborting simply means "stop sending more emails" whereas it does not in any way "unsend" already sent messages.  

Either when all emails are sent or when the abort button is clicked, it serves another purpose: a reset button.  Simply resets the counter and switches back to abort mode, ready for the next batch.

# Advanced Configuration

This is the section to pay attention to, because it lets you do some powerful things.

## Multithreading

Multithreading has been an obvious feature from the beginning.  Simply put, instead of sending one email at a time, we can now send many at once.  Of course, there are limitations to this, such as Python's Global Interpreter Lock and the limitations of processor multitasking, but I have seen an increase in performance.

There are three modes of multithreading supported:

### No Multithreading (MT-NONE)

This sends all the emails from one thread, one after another.  It was the first mode implemented and is likely the most foolproof here.  You will notice that on the radioselector for the `None` option, there is a number entry box.  This entry box specifies the number of seconds between one email send completion and the next beginning.  

At first, intentionally delaying the email time can seem useless.  However, it does have advantages.  First, Gmail limits users to 500 emails per rolling 24 hours.  Settings the number of emails to 500 and the delay to 180 secnods will allow the sender to simply roll right into the next period of 24 hours and send emails at a continous rate.  It could also be used to bypass/decrease likeliehood of spam detection, as bots like this one tend to send emails very quickly and slowing that rate down can avoid being flagged as spam.

### Limited Multithreading (MT-LIM)

This mode is desiged to spawn a specific number of threads, each sending a specific number of emails.  It allows for the quantity of emails to be split up nicely into worker threads without spawning insane amounts of threads.  Usually, I aim for around the square root of the number of total emails to be sent for each thread, for example:

> Let's say we're sending 100 emails.
> I want to use limited multithreading mode.
> I take sqrt(100) = 10, and decide to use 10 threads sending 10 emails each.

> Let's say we're sending 9,000 emails.
> I want to use limited multithreading mode.
> I take sqrt(9000) = 94.86, so I decide to use 90 threads with 100 emails each.

If you don't like the sound of 90 worker threads (I don't), you could also play around with the numbers a bit and use 9 threads with 1000 emails each.

The numerical entry field next to the `Limited:` radioselector is the number of threads to be spawned.

*Note*: When using Gmail, I have found that sending with more than 15 threads tends to cause SMTP 421 errors (`Service not available, closing transmission channel`).  Other users doing similar tasks report that this error seems to be thrown in the case of too many concurrent connections to Gmail's SMTP server from 1 IP address.

### Unlimited Multithreading (MT-ULIM)

The opposite of MT-NONE, which sends all emails in 1 thread:  MT-ULIM sends 1 email per thread.  In as many threads as there are emails to send.

I do not recommend using this mode for quantities above 100 emails, as I have found it to quickly hog system resources.  However, for smaller quantities, it can be quite fast.

## Connection Controls

This is the section that directly affects how many connections are made to the server.

### Max Retries

The value entered in the `Max. Retries` entry box is the maximum number of times the program will attempt to send an email before discarding it and moving on.  It defaults to 5.

### Connect Once

This mode will establish one connection to the server (per thread) and maintain that connection to send emails.  It typically results in less likliehood of an SMTP 421 error, however, if that connection gets dropped, then that thread decreases its retry count by one.  If it reaches max retries, it gives up entirely -- which could result in not all emails being sent.

In short, this mode allows a faster but slightly less reliable mode of delivering emails.

### Connect per send

This mode will establish one connection, send one email, drop the connection, and repeat.  It may result in a greater likliehood of an SMTP 421 error, however, if it doesn't trigger the spam detection, then it delivers emails much more reliably as the max retries setting applies to each individual email as opposed to all of them.

In short, this mode allows for a slower but slightly more reliable mode of delivering emails.
