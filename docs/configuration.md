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

