===============
IRC Standup Bot
===============

A simple script to provide automated cat herding for IRC-based standups.

Schedule the bot to run via a cron job, and it'll connect to your IRC server,
join the given channel, ping all the meeting attendees (even if they're not in
the meeting channel), and thank the participants when the meeting is over.

------------
Installation
------------

Clone this repo, and install the project's dependencies (perhaps in a
virtualenv)::

   $ pip install -r requirements.txt

And then just run the script directly.

-----
Usage
-----

::

    $ python bot.py --help
    usage: bot.py [-h] [--port PORT] [--standup-duration STANDUP_DURATION]
                  server channel nickname nickname-to-ping [nickname-to-ping ...]

    positional arguments:
      server                The IRC server to connect to.
      channel               The IRC channel to hold the standup in.
      nickname              The IRC nickname to use.
      nickname-to-ping      List of users to ping at the beginning of the standup.

    optional arguments:
      -h, --help            show this help message and exit
      --port PORT           The IRC server's port.
      --standup-duration STANDUP_DURATION
                            Standup duration in seconds (the default is 15
                            minutes).

So, you can use cron to schedule a standup every weekday at 17:00 UTC (server
time) with `dolphm`, `dstanek`, and `lbragstad` on Freenode in the
`#standup-channel` (the `#` prefix is optional; use quotes if you want to
specify a `"##private-channel"` like so::

    0 17 * * 1-5 python ~/irc-standup-bot/bot.py chat.freenode.net standup-channel dolph_bot dolphm dstanek lbragstad
