"""IRC standup bot."""

import irc.client
import irc.strings


USERS = [
    'dolphm',  # Dolph Mathews
    'lbragstad',  # Lance Bragstad
    'dstanek',  # David Stanek
    'rderose',  # Ron de Rose
    'nputschi',  # Navid Putschi
    'nonameentername',  # Werner ...
    'jorge_munoz']  # Jorge Munoz


class StandupBot(irc.client.SimpleIRCClient):
    """IRC bot to run daily standups.

    Connects to IRC, runs a standup, and disconnects.

    """

    def __init__(self, channel, nickname, server, port=6667):
        """Initialize the IRC client."""
        super(StandupBot, self).__init__()

        print('Connecting...')
        self.connect(server, port, nickname)
        self.channel = channel

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

        # Disconnect after 15 minutes.
        connection.execute_delayed(delay=60 * 15, function=connection.quit)

    def on_disconnect(self, connection, event):
        """Exit cleanly."""
        raise SystemExit()

    def on_namreply(self, connection, event):
        """Start the standup."""
        if self._already_started_standup:
            return

        self._already_started_standup = True

        list_of_names = event.arguments[-1].split(' ')

        # Strip user modes from names.
        list_of_names = [x.lstrip('@') for x in list_of_names]

        # Filter list of names for ones we care about.
        list_of_names = [x for x in list_of_names if x in USERS]

        # Build a pretty ping message.
        comma_separated_names = ', '.join(sorted(list_of_names))
        message = '%s: standup time!' % comma_separated_names

        # Send the standup message.
        connection.privmsg(self.channel, message)
        connection.privmsg(self.channel, 'What are you working on today, and '
                                         'what do you need help with?')

        for user in USERS:
            if user not in list_of_names:
                connection.privmsg(user, 'Standup time in #osic-keystone')

    def on_pubmsg(self, connection, event):
        """Do nothing."""
        print(
            'Received pubmsg: %s (source=%s, type=%s, target=%s, '
            'arguments=%s, tags=%s)' % (
                event,
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
                event,
                event.source,
                event.type,
                event.target,
                event.arguments,
                event.tags))


if __name__ == "__main__":
    bot = StandupBot(
        channel='#osic-keystone',
        nickname='dolphm_bot',
        server='chat.freenode.net',
        port=6667)
    bot.start()
