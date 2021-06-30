"""This cog allows Chatango users to interact with their `Matches <https://idleuser.com/projects/matches>`_ account.
"""
import asyncio
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from time import sleep

from discord.ext import commands

import config
from lib import ch
from utils import checks
from utils.fjclasses import ChatangoUser, Match, DbHelper

chbot = None

logger = logging.getLogger(__name__)


class Chatango(commands.Cog):
    """The Chatango cog class."""

    def __init__(self, bot):
        self.bot = bot
        self.current_match = None
        self.bot.loop.create_task(self.chatango_bot_task())
        self.bot.loop.create_task(self.chatango_log_task())

    def __unload__(self):
        chbot.stop()

    class ChBot(ch.RoomManager):
        """The Chatango bot. A hacky way of having the Discord bot interact with a different website."""

        def onInit(self):
            """Called on init. Required."""
            global chbot
            chbot = self
            self.season = 4  # the current Match season
            self.buffer = []  # list of messages to relay back to Discord
            self.users = []  # the users in the chatroom(s)
            self.setNameColor('000099')
            self.setFontColor('000099')
            self.setFontFace('Times')
            self.setFontSize(14)

        def onMessage(self, room, author, message):
            """Called when the bot receives a message in a room. Message is logged and handled.

            :param room: The room the message was sent in.
            :param author: The author of the message.
            :param message: The message received.
            """

            # log in discord channel
            if 'fjbot' in message.body.lower() or author.name == self.name.lower():
                msg = '[{}] {}: {}'.format(room.name, author.name, message.body)
                self.buffer.append(msg)
            self.message_handler(author, message.body)
            # room.message('@{}, {}'.format(author.name, msg))

        def onPMMessage(self, pm, author, message):
            """Called when the bot receives a private message. Message is logged and handled.

            :param pm: The room the message was sent in.
            :param author: The author of the message.
            :param message: The message received.
            """
            msg = '[PM] {}: {}'.format(author.name, message)
            self.buffer.append(msg)
            self.message_handler(author, message)

        def onFloodWarning(self, room):
            """Called when the bot receives a warning. Message is logged.

            :param room: The room the warning was received in.
            """
            logger.warning('onFloodWarning:{}'.format(room))

        def onFloodBan(self, room):
            """Called when the bot receives a ban. Message is logged.

            :param room: The room the ban was received in.
            """
            logger.warning('onFloodBan:{}'.format(room))

        def sendRoomMessage(self, room, msg):
            """Sends a message to a room.

            :param room: The room to send the message to.
            :param msg: The message received.
            :return: `True` if message was sent, `False` otherwise.
            """
            room = self.getRoom(room)
            if room:
                room.message(msg)
                return True
            return False

        def sendUserMessage(self, user, msg):
            """Sends a message to a specific user through PM.

            :param user: The user to send the message to.
            :param msg: The message to send.
            """
            try:
                if sys.getsizeof(msg) > 800:
                    tokens = msg.split()
                    mid = round(len(tokens) / 2)
                    self.pm.message(
                        ch.User(user.name), '{} ...'.format(' '.join(tokens[:mid]))
                    )
                    sleep(0.5)
                    self.pm.message(
                        ch.User(user.name), '... {}'.format(' '.join(tokens[mid:]))
                    )
                else:
                    self.pm.message(ch.User(user.name), msg)
                    msg = '[RESP] {}: {}'.format(user.name, msg)
                    self.buffer.append(msg)
            except Exception as e:
                logging.error('Failed to PM User:{} - {}'.format(user.name, e))

        def message_handler(self, author, message):
            """Reads through the original message and checks to see if a command is requested.

            .. Note:
                The message is checked to see if it begins with default prefix, the message is ignored if it does not.
                If the check is successful, any further command aside from `register` and requesting a Discord server
                invite link notifies the user to register before using any other commands.

                If the user is registered and is not requesting an invite link, the command is sent for further
                processing.

            :param author: The author of the message.
            :param message: The message to handle.
            """
            if author.name != self.name.lower() and message.startswith(
                config.base['default_prefix']
            ):
                args = message.lower().split(' ')
                user = ChatangoUser(author)
                if '!discord' in args[0]:  # Discord invite link
                    msg = 'Discord Channel: {}'.format(config.base['invite']['guild'])
                    self.sendUserMessage(user, msg)
                elif (
                    not user.is_registered() and 'register' not in args[0]
                ):  # user is not registered
                    msg = (
                        'You must first register to use commands. '
                        'Please use command `!register`.'
                    )
                    self.sendUserMessage(user, msg)
                else:  # user is registered
                    msg = '[CMD] {}: {}'.format(user.name, message)
                    self.buffer.append(msg)
                    self.command_handler(user, args[0], args[1:])

        def command_handler(self, user, cmd, args=[]):
            """Checks the command and sends it for final processing. A response is sent back to the user.

            .. Note:
                All responses back to the user are sent through PM to avoid flooding the chatroom.

            :param user: The user submitting the command.
            :param cmd: The command to look for.
            :param args: The parameters for the command.
            """
            cmd = cmd.lower()
            msg = False
            if cmd == '!register':
                msg = self.register(user)
            elif cmd == '!login':
                msg = self.login_link(user)
            elif cmd == '!help':
                msg = (
                    '!discord - Discord invite link | '
                    '!login - Login link | '
                    '!reset - Reset password | '
                    '!reset-password - Reset password | '
                    '!rate - Rate the current match | '
                    '!stats - View your stats | '
                    '!bet - Bet points on a current Match | '
                    '!rumble - Get your entry number for the Royal Rumble (seasonal)'
                )
            elif cmd == '!reset' or cmd=='!reset-password':
                msg = self.reset_pw(user)
            elif cmd in ['!mypoints', '!points', '!mystats', '!stats']:
                msg = user.stats_text(season=4)
            elif cmd == '!rate':
                msg = self.rate_match(user, args)
            elif cmd == '!bet':
                msg = self.bet_match(user, args)
            elif cmd == '!rumble':
                msg = self.join_rumble(user)
            elif cmd == '!matches':
                msg = self.open_matches(user)
            else:
                res = user.chatroom_command(cmd)
                if res['success']:
                    msg = res['message']
                    if '@mention' in res:
                        msg = msg.replace('@mention', user.mention)
                else:
                    msg = (
                        'Command not found for `{}`. '
                        'Use !help to get a list of commands.'.format(cmd)
                    )
            if msg:
                self.sendUserMessage(user._author, msg)

        def register(self, user):
            """Registers the user.

            .. Note::
                The user is registered using their Chatango name. If a user already exists with the same name, the
                registration will fail. This would have to be resolved manually.

            :param user: The user to register.
            :return: The response message for the user.
            """
            if user.is_registered():
                return (
                    '{}, you are already registered. '
                    'Use `!help` to get a list of commands'.format(user.mention)
                )
            response = user.register()
            if response['success']:
                logger.info('`{}` has registered'.format(user.name))
                return (
                    '{}, registration was successful! '
                    'You can now use !login to get a quick login link for the website. '
                    'Remember to set a password for your account by using '
                    '`!resetpw`. For other commands, use `!help`.'.format(user.mention)
                )
            else:
                logger.error('Failed to register: `{}`'.format(user.name))
                return response['message']

        def login_link(self, user):
            """Sends a quick login link to the Matches website.

            ..  Note:
                The hyperlink can only be used once and within a short time frame before it expires.

            :param user: The user submitting the command.
            :return: The response message for the user.
            """
            link = user.request_login_link()
            logger.info('`{}` requested a login link'.format(user.name))
            return '{} (link expires in 5 minutes)'.format(link)

        def reset_pw(self, user):
            """Sends a quick reset password link for the Matches website.

            ..  Note:
                The hyperlink can only be used once and within a short time frame before it expires.

            :param user: The user submitting the command.
            :return: The response message for the user.
            """
            link = user.request_reset_password_link()
            logger.info('`{}` requested a change password link'.format(user.name))
            return '{} (Link will expire in 30 minutes)'.format(link)

        def rate_match(self, user, args=[]):
            """Adds the user's rating to the most recently closed `Match`.

            .. Note:
                If no `Match` id is provided, the rating is added to the most recently closed `Match`.

            :param user: The user submitting the command.
            :param args: The list of arguments received. Only the first value is checked. Must cast to type `float`.
            :return: The response message for the user.
            """
            if not args:
                return 'Missing a valid rating. Command: !rate [number]'
            try:
                rating = float(args[0])
            except ValueError:
                return 'Not a valid rating'
            rows = user.search_match_by_recent_completed()
            if not rows:
                return 'No current match set to rate'
            match = Match(id=rows[0].id)
            res = user.rate_match(match.id, rating)
            if res['success']:
                logger.info(
                    '`{}` rated `Match {}` `{}` stars'.format(
                        user.name, match.id, rating
                    )
                )
                return '{} Star Match rating received for: {}'.format(
                    rating, match.info_text_short()
                )
            else:
                return res['message']

        def bet_match(self, user, args=[]):
            """Submits a bet for a `Match`.

            .. Note:
                Refers the user to use the `!login` command instead.

                This function might never get completed.

            :param user: The user submitting the command.
            :param args: The list of arguments received. None are used.
            :return: The response message for the user.
            """
            return 'Full command not available yet on Chatango. Use !login'

        def join_rumble(self, user, args=[]):
            """Provides a quick login link to the website's Royal Rumble page.

            :param user: The user submitting the command.
            :param args: The list of arguments received. None are used.
            :return: The response message for the user.
            """
            logger.info('`{}` requested a rumble link'.format(user.name))
            link = user.request_login_link()
            link = link.replace('projects/matches?', 'projects/matches/royalrumble?')
            return 'Join the rumble here! {} (link expires in 5 minutes)'.format(link)

        def open_matches(self, user):
            """Sends a list of open-bet Matches.

            .. Note::
                A short-view in plain text is sent, as Chatango does not support rich text.

            :param user: The user submitting the command.
            :return: The response message for the user.
            """
            rows = user.search_match_by_open_bets()
            if rows:
                matches = [Match(row.id) for row in rows]
                matches_info = [
                    '[{} - {}]'.format(m.match_type, m.contestants) for m in matches
                ]
                return ' | '.join(matches_info)
            else:
                return 'No Open Matches available.'

    def start_chbot(self):
        """Initializes and start the Chatango bot."""
        self.ChBot.easy_start(
            config.chatango['rooms'],
            config.chatango['username'],
            config.chatango['secret'],
        )

    async def chatango_bot_task(self):
        """Creates a separate thread for the Chatango bot.

        .. Note::
            A thread is required as the Chatango bot is not asynchronous.
        """
        await self.bot.wait_until_ready()
        logger.info('START ChatangoBot thread')
        executor = ThreadPoolExecutor()
        t_stream = Thread(target=self.start_chbot)
        await self.bot.loop.run_in_executor(executor, t_stream.start)
        await self.bot.loop.run_in_executor(executor, t_stream.join)
        logger.info('END ChatangoBot `{}` thread'.format(chbot.name))
        await self.chatango_bot_task()

    async def wait_until_chbot_running(self, limit=30):
        """Checks to see if the Chatango bot is running.

        .. Note:
            Checks are made in 1-second intervals.

        :param limit: The amount of times to check before failing. Default is 30.
        :return: `True` if the Chatango bot is running, `False` otherwise
        """
        attempt = 1
        while attempt < limit:
            try:
                return chbot._running is True
            except Exception as e:
                logger.debug(
                    'wait_until_chbot_running: Attempt - {}/{}, Msg - {}'.format(
                        attempt, limit, e
                    )
                )
            await asyncio.sleep(1)
            attempt = attempt + 1

    async def chatango_log_task(self):
        """Cycles through the Chatango bot's message buffer and sends content to a defined Discord channel."""
        global chbot
        await self.bot.wait_until_ready()
        await self.wait_until_chbot_running()
        chbot.bot = self.bot
        channel_chatango = self.bot.get_channel(config.base['channel']['chatango'])
        logger.info('START chatango_log_task')
        while not self.bot.is_closed() and chbot._running:
            while chbot.buffer:
                await channel_chatango.send('```\n{}\n```'.format(chbot.buffer.pop(0)))
                await asyncio.sleep(0.5)
            await asyncio.sleep(1)
        logger.info('END chatango_log_task')

    @commands.command(name='chatango-send', aliases=['ch-send'])
    @commands.is_owner()
    async def send_message(self, ctx, *, message: str):
        """Sends a message to all of the rooms the Chatango bot is a member of.

        .. Note::
            Only the bot owner can use this.

        :param ctx: The invocation context.
        :param message: The message to send.
        """
        await ctx.send('Send message to Chatango? [Y/N]\n```{}```'.format(message))
        confirm = await self.bot.wait_for('message', check=checks.confirm, timeout=10.0)
        if confirm and confirm.content.upper() == 'Y':
            ch_rooms = []
            for ch_room in config.chatango['rooms']:
                if chbot.sendRoomMessage(ch_room, message):
                    ch_rooms.append(ch_room)
            await ctx.send(
                '{}, Discord message sent to Chatango [{}].'.format(
                    ctx.author.mention, ','.join(ch_rooms)
                )
            )
        else:
            await ctx.send('{}, Chatango message cancelled.'.format(ctx.author.mention))

    @commands.command(name='chatango-users', aliases=['ch-users', 'ch-user-list'])
    @commands.is_owner()
    async def display_users(self, ctx):
        """Displays a list of all the Chatango users the Chatango bot has read messages from.

        .. Note::
            Only the bot owner can use this.

        :param ctx: The invocation context.
        """
        await ctx.send(
            '```Chatango User List ({})\n{}\n```'.format(len(chbot.users), chbot.users)
        )


def setup(bot):
    """Required for cogs.

    :param bot: The Discord bot.
    """
    bot.add_cog(Chatango(bot))
