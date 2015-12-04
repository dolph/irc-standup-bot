# Copyright 2013 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""IRC standup bot."""

import argparse
import ssl

import irc.client
import irc.connection
import irc.strings


class StandupBot(irc.client.SimpleIRCClient):
    """IRC bot to run daily standups.

    Connects to IRC, runs a standup, and disconnects.

    """

    def __init__(self, channel, nickname, server, port=6667, use_ssl=False,
                 password=None, users_to_ping=None, standup_duration=60 * 15,
                 topic='Standup meeting', nickserv_password=None):
        """Initialize the IRC client."""
        super(StandupBot, self).__init__()
        self.channel = channel
        self.users_to_ping = users_to_ping or []
        self.standup_duration = standup_duration
        self.topic = topic
        self.nickname = nickname
        self.nickserv_password = nickserv_password

        # We'll use this to track who, of the people we pinged, said anything.
        self.participants = set()

        print('Connecting...')
        if use_ssl:
            connect_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
        else:
            connect_factory = irc.connection.Factory()
        self.connect(server, port, nickname, password=password,
                     connect_factory=connect_factory)

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
        if self.nickserv_password:
            print('Identifying with NickServ...')
            # TODO(dolph): should wait for nickserv response before joining a
            # channel that might require it.
            connection.privmsg(
                'NickServ', 'IDENTIFY %s %s' % (self.nickname, self.nickserv_password))

        print('Joining %s...' % self.channel)
        connection.join(self.channel)

        print('Requesting names on channel...')
        connection.names(self.channel)

        # Disconnect later, after the standup is over.
        print('Disconnecting after %d seconds.' % self.standup_duration)
        connection.execute_delayed(
            delay=self.standup_duration,
            function=self.end_standup)

    def end_standup(self):
        """End the standup by thanking participants."""
        if self.participants:
            users_to_thank = ', '.join(sorted(list(self.participants)))
            self.connection.privmsg(
                self.channel, 'Thank you, %s!' % users_to_thank)

        self.connection.quit()

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
        list_of_names = [x.lstrip('@').lstrip('+') for x in list_of_names]

        # Filter list of names for ones we care about.
        list_of_names = [x for x in list_of_names if x in self.users_to_ping]

        # Build a pretty ping message.
        message = ''
        if list_of_names:
            message = ', '.join(sorted(list_of_names))
            message += ': '
        message += self.topic

        # Send the standup ping.
        connection.privmsg(self.channel, message)
        connection.privmsg(self.channel, 'What are you working on today, and '
                                         'what do you need help with?')

        # Ping the users that are not in the channel privately.
        for user in self.users_to_ping:
            if user not in list_of_names:
                connection.privmsg(
                    user, '%s in %s' % (self.topic, self.channel))

    def on_pubmsg(self, connection, event):
        """Do nothing."""
        nickname = event.source.split('!', 1)[0]
        if nickname in self.users_to_ping:
            self.participants.add(nickname)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'server', help='The IRC server to connect to.')
    parser.add_argument(
        '--port', type=int, default=6667, help='The IRC server\'s port.')
    parser.add_argument(
        '--password', help='The IRC server\'s password.')
    parser.add_argument(
        '--ssl',
        action='store_true', default=False,
        help='The IRC server requires SSL.')
    parser.add_argument(
        'channel', help='The IRC channel to hold the standup in.')
    parser.add_argument(
        'nickname', help='The IRC nickname to use.')
    parser.add_argument(
        '--nickserv-password', help='The NickServ password to use.')

    parser.add_argument(
        'users_to_ping',
        metavar='nickname-to-ping', type=str, nargs='+',
        help='List of users to ping at the beginning of the standup.')

    parser.add_argument(
        '--standup-duration',
        type=int, default=60 * 15,
        help='Standup duration in seconds (the default is 15 minutes).')

    parser.add_argument(
        '--topic',
        default='Standup meeting',
        help='What to invite everyone to')

    args = parser.parse_args()

    # Prefix the channel name with a '#' if it doesn't already have one.
    if not args.channel.startswith('#'):
        args.channel = '#%s' % args.channel

    bot = StandupBot(
        channel=args.channel,
        nickname=args.nickname,
        nickserv_password=args.nickserv_password,
        server=args.server,
        port=args.port,
        password=args.password,
        use_ssl=args.ssl,
        users_to_ping=args.users_to_ping,
        topic=args.topic,
        standup_duration=args.standup_duration)
    bot.start()
