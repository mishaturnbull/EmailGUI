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
        2.4.1 [Verify Recipient Address](#verify-button)  
        2.4.2 [Recipient Address](#recipient-address)  
    2.5 [Server](#server)  
    2.6 [Message text](#message)  
    2.7 [Attachments](#attachments)  
        2.7.1 [Browse button](#the-browse-button)  
    2.8 [Progress indicator](#status-indicator)  

3.0 [Advanced configuration](#advanced-configuration)  

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
[2.4.1 To Address](#recipient-address): The address to send emails to  
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
email1@gmail.com   ---.
email2@gmail.com   ----+-.
email3@gmail.com   ----+--+--> recipient@myserver.com
email4@gmail.com   ---`
```

Of course, you can also just use 1 email account to send from.  I'd recommend using 1 if you're sending using the same server that's receiving, but if you have to go across the internet at all (as opposed to remaining on local intranet, or even better the same machine) then using multiple accounts may be a better idea.

### From addresses

Put the email acounts to send mail from in this line.  If you want to use more than one, separate them with commas.  Whitespace is automatically removed and should not be a factor.

### From passwords

This is where the password goes to the email address you're sending from.  If you have more than 1 account, you can enter the same number of passwords, comma-separated.  If you have multiple accounts dedicated for stressing email servers (like I do) and they all have the same password (bad!  don't do that!), you can simply enter that password once and the program will automatically fill in the rest.

### Forge from account

What could be more fun than emailing your sysadmin as your sysadmin?  Nothing!  The field to the right of the from address entry allows you to enter text that will be replaced in all relevant from tags.  This will get you as close as possible to sending mail as the account you enter there.

***THIS CAN BE USED TO DO BAD AND/OR ILLEGAL THINGS.  IF YOU DO BAD THINGS, I DO NOT CLAIM ANY RESPONSIBILITY FOR YOUR ACTIONS.***

