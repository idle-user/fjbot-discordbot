"""This cog handles scheduled messages to a channel."""
import asyncio
import datetime
import logging

import discord
from discord.ext import tasks, commands

import config
from utils import checks, quickembed
from utils.fjclasses import DbHelper, DiscordUser

logger = logging.getLogger(__name__)


class Scheduler(commands.Cog):
    """The Scheduler cog class."""

    def __init__(self, bot):
        self.bot = bot
        self.scheduled_payloads = {}
        self.check_registered_users.start()
        self.check_scheduler.start()
        self.bot.loop.create_task(self.showtime_schedule_task())

    @tasks.loop(minutes=1.0)
    async def check_scheduler(self):
        """A routine task that checks for the weekly schedule and updates pending items when appropriate.

        .. Note::
            This task is executed every minute to check for an update. New tasks are created by sending it to
            :func:`cogs.scheduler.scheduler_task`.

        .. Important::
            Python 3.7 does not have an easy way for naming a task. A dictionary of tasks is created and handled
            instead.
        """
        await self.bot.wait_until_ready()
        now = datetime.datetime.now()
        key_flag = '%s_flag' % now.strftime('%A').lower()
        scheduler_list = DbHelper().chatroom_scheduler_list()
        # check if pending tasks match
        for payload in scheduler_list:
            if payload['name'] in self.scheduled_payloads:
                if (
                    payload.items()
                    != self.scheduled_payloads[payload['name']]['data'].items()
                ):
                    logger.info(
                        'Found difference in pending task - `{}`'.format(
                            payload['name']
                        )
                    )
                    self.scheduled_payloads[payload['name']]['task'].cancel()
                    await self.scheduled_payloads[payload['name']]['task']

            task_dt = datetime.datetime.combine(
                datetime.date.today(),
                (datetime.datetime.min + payload['start_time']).time(),
            )
            # add new task
            if (
                payload['active']
                and payload[key_flag]
                and task_dt > now
                and payload['name'] not in self.scheduled_payloads
            ):
                self.scheduled_payloads[payload['name']] = {}
                self.scheduled_payloads[payload['name']]['data'] = payload
                self.scheduled_payloads[payload['name']]['task_datetime'] = task_dt
                self.scheduled_payloads[payload['name']]['task_wait_time'] = (
                    task_dt - now
                ).total_seconds()
                payload_task = self.bot.loop.create_task(self.scheduler_task(payload))
                # 3.8 has ability to set name to task, but currently on 3.7
                self.scheduled_payloads[payload['name']]['task'] = payload_task

    async def scheduler_task(self, payload):
        """Handles a single weekly scheduled message by creating the message and sleeping until the appropriate time
        defined in the message.

        .. important::
            The channel the message is sent to is defined in :mod:`config`.
            Modify where appropriate for your own Discord server.

        :param payload: The event details to deliver. See :func:`utils.fjclasses.DbHelper.chatroom_scheduler_list`.
        """
        try:
            role_name = ''
            embed = quickembed.info(desc='Event')
            embed.add_field(name=payload['message'], value='\u200b', inline=False)
            if payload['name'] in ['RAW', 'SmackDown', 'NXT']:
                channel = self.bot.get_channel(config.base['channel']['wwe'])
                role_name = 'WWE-{}-Squad'.format(payload['name'])
            elif 'AEW' in payload['name']:
                channel = self.bot.get_channel(config.base['channel']['aew'])
                role_name = 'AEW-Squad'
            elif 'Dev-Test' in payload['name']:
                channel = self.bot.get_channel(config.base['channel']['bot-test'])
                role_name = 'Admin'
            else:
                channel = self.bot.get_channel(config.base['channel']['general'])
            logger.info(
                'Task scheduled - channel:`{}` name:`{}` sleep_until:`{}`'.format(
                    channel.name,
                    payload['name'],
                    self.scheduled_payloads[payload['name']]['task_datetime'],
                )
            )
            await asyncio.sleep(
                self.scheduled_payloads[payload['name']]['task_wait_time']
            )
            # final check before sending message
            if (
                channel
                and payload['name'] in self.scheduled_payloads
                and payload.items()
                == self.scheduled_payloads[payload['name']]['data'].items()
            ):
                msg = ''
                if role_name:
                    role = discord.utils.get(channel.guild.roles, name=role_name)
                    msg = '{}'.format(role.mention)
                await channel.send(msg, embed=embed)
                if payload['tweet']:
                    await self.bot.tweet(payload['tweet'])
            else:
                logger.info(
                    'Task message not sent. Payload does not match. - `{}`'.format(
                        payload['name']
                    )
                )
        except asyncio.CancelledError:
            logger.info('Task Cancelled - `{}`'.format(payload['name']))
        finally:
            del self.scheduled_payloads[payload['name']]
            logger.info('Task End - `{}`'.format(payload['name']))

    @commands.command(name='scheduler', hidden=True)
    @commands.is_owner()
    @checks.is_registered()
    async def scheduler_pending(self, ctx):
        """Displays a list of pending alert messages.

        .. note::
            Only the bot owner can use this.

        :param ctx: The invocation context.
        """
        if self.scheduled_payloads.items():
            user = DiscordUser(ctx.author)
            embed = quickembed.info(desc="Today's Scheduled Alerts (PT)", user=user)
            embed.add_field(
                name='\u200b',
                value='\n'.join(
                    [
                        '{1} - **{0}**'.format(k, v['task_datetime'])
                        for k, v in self.scheduled_payloads.items()
                    ]
                ),
            )
        else:
            embed = quickembed.error(desc='Nothing scheduled for today')
        await ctx.send(embed=embed)

    @commands.command(name='tw', hidden=True)
    @commands.is_owner()
    async def tw(self, ctx, *, message: str):
        await self.bot.tweet(message)

    async def showtime_schedule_task(self):
        """Retrieves the closest event from the database and creates a scheduled message to post to a channel.

        .. important::
            The channel the message is sent to is defined in :mod:`config`.
            Modify where appropriate for your own Discord server.
        """
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            event_list = DbHelper().future_events()
            if not event_list:
                await asyncio.sleep(60)
                continue
            event = event_list[0]
            dt = datetime.datetime.now()
            event_start_timer = (event['date_time'] - dt).total_seconds()
            embed = quickembed.info(desc='Event')
            embed.add_field(
                name='{} has begun!'.format(event['name']), value='\u200b', inline=False
            )
            event_length_timer = 14400
            if event['ppv']:
                channel = self.bot.get_channel(config.base['channel']['ppv'])
            else:
                await asyncio.sleep(60)
                continue
            logger.info(
                'showtime_schedule_task: channel:`{}` events:`{}` sleep until:`{}`'.format(
                    channel.name,
                    event['name'],
                    dt + datetime.timedelta(seconds=event_start_timer),
                )
            )
            await asyncio.sleep(event_start_timer)
            if channel:
                role = discord.utils.get(channel.guild.roles, name='PPV-Squad')
                await channel.send(role.mention, embed=embed)
                activity = discord.Activity(
                    type=discord.ActivityType.watching, name=event['name']
                )
                tweet_msg = '{} has begun! discuss the live event with us in our WatchWrestling Discord. #WatchWrestling #discord\n\nhttps://discord.gg/U5wDzWP8yD'.format(
                    event['name']
                )
                await self.bot.tweet(tweet_msg)
                await self.bot.change_presence(activity=activity)
                await asyncio.sleep(event_length_timer)
                await self.bot.change_presence(activity=None)
        logger.info('END showtime_schedule_task')


    @tasks.loop(minutes=5.0)
    async def check_registered_users(self):
        await self.bot.wait_until_ready()
        guild = self.bot.get_guild(config.base['guild_id'])
        role = guild.get_role(753640365612990546)
        members = guild.members
        for member in guild.members:
            user = DiscordUser(member)
            is_registered = user.is_registered()
            has_role = role in member.roles
            if is_registered and not has_role:
                await member.add_roles(role)
                logger.info('Added @registered to: {}'.format(user.name))
            elif not is_registered and has_role:
                await member.remove_roles(role)
                logger.info('Removed @registered from: {}'.format(user.name))


def setup(bot):
    """Required for cogs.

    :param bot: The Discord bot.
    """
    bot.add_cog(Scheduler(bot))
