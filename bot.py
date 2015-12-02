"""IRC standup bot."""

import argparse

import irc.client
import irc.strings


class StandupBot(irc.client.SimpleIRCClient):
    """IRC bot to run daily standups.

    Connects to IRC, runs a standup, and disconnects.

    """

    def __init__(self, channel, nickname, server, port=6667,
                 users_to_ping=None, standup_duration=60 * 15):
        """Initialize the IRC client."""
        super(StandupBot, self).__init__()
        self.channel = channel
        self.users_to_ping = users_to_ping or []
        self.standup_duration = standup_duration

        print('Connecting...')
        self.connect(server, port, nickname)

        # We start the standup as soon as we know who is in the channel. But
        # for some reason, we get two responses when we request the list of
        # names once. This variable allows us to ignore the second list when
        # we've already started standup time.
        self._already_started_standup = False

        print('Waiting for welcome message...')

    def on_nicknameinuse(self, c, e):
        """Handle nickname conflicts."""
        print('Nickname in use!')
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, connection, event):
        """Handle welcome message from server."""
        print('Joining %s...' % self.channel)
        connection.join(self.channel)

        print('Requesting names on channel...')
        connection.names(self.channel)

        # Disconnect later, after the standup is over.
        print('Disconnecting after %d seconds.' % self.standup_duration)
        connection.execute_delayed(
            delay=self.standup_duration,
            function=connection.quit,
            arguments=('Standup ended!',))

    def on_disconnect(self, connection, event):
        """Exit cleanly."""
        raise SystemExit()

    def on_namreply(self, connection, event):
        """Start the standup."""
        # Bail if we've already started a standup.
        if self._already_started_standup:
            return
        self._already_started_standup = True

        # The list of names is space-delimited. Break it apart so we can
        # iterate through it.
        list_of_names = event.arguments[-1].split(' ')

        # Strip user modes from names.
        list_of_names = [x.lstrip('@') for x in list_of_names]

        # Filter list of names for ones we care about.
        list_of_names = [x for x in list_of_names if x in self.users_to_ping]

        # Build a pretty ping message.
        message = ''
        if list_of_names:
            message = ', '.join(sorted(list_of_names))
            message += ': '
        message += 'Standup time!'

        # Send the standup message.
        connection.privmsg(self.channel, message)
        connection.privmsg(self.channel, 'What are you working on today, and '
                                         'what do you need help with?')

        # Ping the users that are not in the channel privately.
        for user in self.users_to_ping:
            if user not in list_of_names:
                connection.privmsg(user, 'Standup time in %s' % self.channel)

    def on_pubmsg(self, connection, event):
        """Do nothing."""
        print(
            'Received pubmsg: %s (source=%s, type=%s, target=%s, '
            'arguments=%s, tags=%s)' % (
                event.source,
                event.type,
                event.target,
                event.arguments,
                event.tags))

    def on_privmsg(self, connection, event):
        """Do nothing."""
        print(
            'Received privmsg: %s (source=%s, type=%s, target=%s, '
            'arguments=%s, tags=%s)' % (
                event.source,
                event.type,
                event.target,
                event.arguments,
                event.tags))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'server', help='The IRC server to connect to.')
    parser.add_argument(
        '--port', default=6667, help='The IRC server\'s port.')
    parser.add_argument(
        'channel', help='The IRC channel to hold the standup in.')
    parser.add_argument(
        'nickname', help='The IRC nickname to use.')

    parser.add_argument(
        'users_to_ping',
        metavar='nickname-to-ping', type=str, nargs='+',
        help='List of users to ping at the beginning of the standup.')

    parser.add_argument(
        '--standup-duration',
        type=int, default=60 * 15,
        help='Standup duration in seconds (the default is 15 minutes).')

    args = parser.parse_args()

    if not args.channel.startswith('#'):
        args.channel = '#%s' % args.channel

    bot = StandupBot(
        channel=args.channel,
        nickname=args.nickname,
        server=args.server,
        port=args.port,
        users_to_ping=args.users_to_ping,
        standup_duration=args.standup_duration)
    bot.start()
