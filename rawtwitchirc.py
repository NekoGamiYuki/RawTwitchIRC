#!/usr/bin/env python3
"""
Author: NekoGamiYuki
Version: 1.1.0

Description:
A simple program for seeing what twitch sends to clients connected via IRC.

Warning:
Currently does not check if login succeeded. However, you will know if you failed
when the program starts spamming like crazy that it's requesting information from
Twitch without printing out any Twitch chat messages.

More about Twitch IRC can be found here:
https://github.com/justintv/Twitch-API/blob/master/IRC.md
"""

# Imported Modules--------------------------------------------------------------
import socket
import time
import sys

# Global Variables--------------------------------------------------------------
SOCK = None
TWITCH = "irc.chat.twitch.tv"
PORT = 6667  # Not using twitch's SSL capable server's

# Sending configuration
commands_sent = 0
send_time = 0
RATE = 100  # No more than 100 commands sent every 30 seconds (change to 20 if not a moderator)


# Twitch Communication----------------------------------------------------------
def send_info(info: str) -> bool:
    """
    Simple way to send information to twitch's server while making sure not to
    send more commands than twitch allows.

    Args:
        info: The information that will be sent to twitch.

    Returns:
        True: If it is able to send the information
        False: If it is unable to send the information
    """

    # TODO: Limit how often the program sends info

    global commands_sent
    global send_time

    time_elapsed = time.time() - send_time

    if time_elapsed > 30:
        commands_sent = 0
        send_time = time.time()
    if commands_sent < RATE:
        # ??? There's a chance that we might disconnect or have a hiccup
        try:
            # NOTE: Do not loop in an attempt to resend possibly incomplete
            # info as you will face the consequences... 2 hours of waiting
            # here I come...
            if not SOCK.send(info.encode("utf-8")):
                print("Failed to send information. Twitch may have closed our connection.")
                return False
            else:
                return True
        except InterruptedError:
            return False


# Main program -----------------------------------------------------------------
username = ""  # The username of the account you're using to read chat.
oauth = ""  # You can get your oauth here: https://twitchapps.com/tmi/
channels = [""]  # A list of channels to join and read chat from.
timeout = 600  # (10 minutes) Time we'll wait, in seconds, before closing our connection.
tags = True  # If true, program will request that twitch give us more detailed information.

print("Checking for username or oauth.")
if not username or not oauth:
    print("Username or Oauth missing. Exiting.")
    sys.exit()

print("Creating socket.")
# Connect to twitch using TCP and IPV4
SOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SOCK.settimeout(timeout)  #
try:
    print("Connecting socket to twitch.")
    SOCK.connect((TWITCH, PORT))
except socket.error:
    print("Unable to connect socket.")
    SOCK.close()
    print("Exiting.")
    sys.exit()

print("Logging in.")
print("Sending oauth.")
if not send_info("PASS {}\r\n".format(oauth)):
    print("Failed to send oauth.")

print("Sending username: {}".format(username))
if not send_info("NICK {}\r\n".format(username)):
    print("Failed to send username.")

if tags:
    # For an IRCv3 membership; Gives us NAMES, JOIN, PART, and MODE events
    print("Requesting IRCv3 membership.")
    send_info("CAP REQ :twitch.tv/membership\r\n")
    # For enabling USERSTATE, GLOBALUSERSTATE, ROOMSTATE, HOSTTARGET, NOTICE
    # and CLEARCHAT raw commands.
    print("Requesting commands.")
    send_info("CAP REQ :twitch.tv/commands\r\n")
    # For detailed information from messages. Getting stuff like the user's
    # color, emotes, etc...
    print("Requesting tags.")
    send_info("CAP REQ :twitch.tv/tags\r\n")

for channel in channels:
    print("Joining: {}".format(channel))
    if not send_info("JOIN #{}\r\n".format(channel)):
        print("Could not join: {}".format(channel))

while True:
    try:
        print('-'*80)
        print("Requesting information from twitch.")
        try:
            information = SOCK.recv(4096)
        except socket.timeout:
            print("Connection timed out.")
            SOCK.close()
            print("Exiting.")
            sys.exit()

        print("Attempting to decode twitch information.")
        try:
            # ??? utf-8 is required, as twitch is a multi-lingual platform and there are
            # times when a user might post in a character set that isn't ascii, such
            # as when typing in a foreign language. Without utf-8 decoding, the program
            # crashes at the sight of a foreign character.
            information = information.decode("utf-8")
        except UnicodeDecodeError:
            # But sadly, this still has some issues when it comes to unicode.
            # There are times when it is still unable to decode a character, causing
            # the program to crash.
            print("Failed to decode information. Printing raw information instead.")
            print(information)

        if not information:
            print("Received no information.")
        elif information == "PING :tmi.twitch.tv\r\n":  # Ping Pong time.
            print("Received PING, sending PONG.")
            if not send_info("PONG :tmi.twitch.tv\r\n"):
                print("Failed to send PONG.")
            else:
                continue
        else:
            print("TWITCH INFO: {}".format(information))
    except KeyboardInterrupt:
        print("Closing socket and exiting program loop.")
        SOCK.close()
        break

print("Exiting program.")

