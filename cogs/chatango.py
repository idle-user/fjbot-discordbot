import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Thread
from time import sleep

from discord.ext import commands

import config
from lib import ch
from utils import checks
from utils.fjclasses import ChatangoUser, Match

chbot = None


class Chatango(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_match = None
        self.bot.loop.create_task(self.chatango_bot_task())
        self.bot.loop.create_task(self.chatango_log_task())

    def __unload__(self):
        chbot.stop()

    class ChBot(ch.RoomManager):
        def onInit(self):
            global chbot
            chbot = self
            self.season = 3
            self.buffer = []
            self.users = []
            self.setNameColor('000099')
            self.setFontColor('000099')
            self.setFontFace('Times')
            self.setFontSize(14)

        def onMessage(self, room, author, message):
            if 'fjbot' in message.body.lower():
                msg = '[{}] {}: {}'.format(room.name, author.name, message.body)
                self.buffer.append(msg)
            self.message_handler(author, message.body)
            # room.message('@{}, {}'.format(author.name, msg))

        def onPMMessage(self, pm, author, message):
            msg = '[PM] {}: {}'.format(author.name, message)
            self.buffer.append(msg)
            self.message_handler(author, message)

        def onFloodWarning(self, room):
            print('```\n[chatango] onFloodWarning:{}\n```'.format(room))

        def onFloodBan(self, room):
            print('```\n[chatango] onFloodBan:{}\n```'.format(room))

        def sendRoomMessage(self, room, msg):
            room = self.getRoom(room)
            if room:
                room.message(msg)
                return True
            return False

        def sendUserMessage(self, user, msg):
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
            except Exception:
                print('```\n[chatango] Failed to PM User:{}\n```'.format(user.name))

        def message_handler(self, author, message):
            if author.name == self.name.lower() or not message.startswith('!'):
                return
            args = message.lower().split(' ')
            user = ChatangoUser(author)
            if '!discord' in args[0]:
                msg = 'Discord Channel: {}'.format(config.discord['invite_link'])
                self.sendUserMessage(user, msg)
            elif not user.is_registered() and 'register' not in args[0]:
                msg = (
                    'You must first register to use commands. '
                    'Please use command `!register`.'
                )
                self.sendUserMessage(user, msg)
            else:
                self.command_handler(user, args[0], args[1:])

        def command_handler(self, user, cmd, args=[]):
            cmd = cmd.lower()
            msg = False
            if cmd == '!register':
                msg = self.register(user)
            elif cmd == '!login':
                msg = self.login_link(user)
            elif cmd == '!help':
                msg = (
                    '!login - Login link | '
                    '!resetpw - Change password | '
                    '!rate - Rate the current match | '
                    '!stats - View your stats | '
                    '!bet - Bet points on a current Match | '
                    '!rumble - Get your entry number for the Royal Rumble (seasonal)'
                )
            elif cmd == '!resetpw':
                msg = self.reset_pw(user)
            elif cmd in ['!mypoints', '!points', '!mystats', '!stats']:
                msg = user.stats_text(season=3)
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
            if user.is_registered():
                return (
                    '{}, you are already registered. '
                    'Use `!help` to get a list of commands'.format(user.mention)
                )
            response = user.register()
            if response['success']:
                print('```\n[chatango] `{}` has registered\n```'.format(user.name))
                return (
                    '{}, registration was successful! '
                    'You can now use !login to get a quick login link for the website. '
                    'Remember to set a password for your account by using '
                    '`!resetpw`. For other commands, use `!help`.'.format(user.mention)
                )
            else:
                print('```\n[chatango] Failed to register: `{}`\n```'.format(user.name))
                return response['message']

        def login_link(self, user):
            link = user.request_login_link()
            print('```\n[chatango] `{}` requested a login link\n```'.format(user.name))
            return '{} (link expires in 5 minutes)'.format(link)

        def reset_pw(self, user):
            link = user.request_reset_password_link()
            print(
                '```\n[chatango] `{}` requested a change password link\n```'.format(
                    user.name
                )
            )
            return '{} (Link will expire in 30 minutes)'.format(link)

        def rate_match(self, user, args=[]):
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
                print(
                    '```\n[chatango] `{}` rated `Match {}` `{}` stars\n```'.format(
                        user.name, match.id, rating
                    )
                )
                return '{} Star Match rating received for: {}'.format(
                    rating, match.info_text_short()
                )
            else:
                return res['message']

        def bet_match(self, user, args=[]):
            pass

        def royalrumble_entry(self, user, args=[]):
            pass

        def open_matches(self, user):
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
        self.ChBot.easy_start(
            config.chatango['rooms'],
            config.chatango['username'],
            config.chatango['secret'],
        )

    async def chatango_bot_task(self):
        await self.bot.wait_until_ready()
        print('[{}] Chatango Bot: START'.format(datetime.now()))
        executor = ThreadPoolExecutor()
        t_stream = Thread(target=self.start_chbot)
        await self.bot.loop.run_in_executor(executor, t_stream.start)
        await self.bot.loop.run_in_executor(executor, t_stream.join)
        print('[{}] Chatango `{}`: END'.format(datetime.now(), chbot.name))
        await self.chatango_bot_task()

    async def wait_until_chbot_running(self, limit=30):
        while limit > 0:
            try:
                return chbot._running is True
            except AttributeError:
                pass
            await asyncio.sleep(1)
            limit = limit - 1

    async def chatango_log_task(self):
        global chbot
        await self.bot.wait_until_ready()
        await self.wait_until_chbot_running()
        chbot.bot = self.bot
        channel_chatango = self.bot.get_channel(config.discord['channel']['chatango'])
        print('chatango_log_task: START')
        while not self.bot.is_closed() and chbot._running:
            while chbot.buffer:
                await channel_chatango.send('```{}```'.format(chbot.buffer.pop(0)))
                await asyncio.sleep(0.5)
            await asyncio.sleep(1)
        print('chatango_log_task: END')

    @commands.command(name='chsend')
    @commands.is_owner()
    async def send_message(self, ctx, *, message: str):
        await ctx.send('Send message to Chatango? [Y/N]```{}```'.format(message))
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

    @commands.command(name='chusers')
    @commands.is_owner()
    async def display_users(self, ctx):
        await ctx.send(
            '```\nChatango User List ({})\n {}```'.format(len(chbot.users), chbot.users)
        )


def setup(bot):
    bot.add_cog(Chatango(bot))
