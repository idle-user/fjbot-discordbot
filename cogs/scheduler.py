import asyncio
import datetime
import logging

from discord.ext import tasks, commands

import config
from utils import checks, quickembed
from utils.fjclasses import DbHelper, DiscordUser


logger = logging.getLogger(__name__)


class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduled_payloads = {}
        self.check_scheduler.start()

    @tasks.loop(minutes=1.0)
    async def check_scheduler(self):
        await self.bot.wait_until_ready()
        now = datetime.datetime.now()
        key_flag = '%s_flag' % now.strftime('%A').lower()
        key_time = '%s_time' % now.strftime('%A').lower()
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
                (datetime.datetime.min + payload[key_time]).time(),
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
        try:
            embed = quickembed.info(desc='Event')
            embed.add_field(name=payload['message'], value='\u200b', inline=False)
            if payload['name'] in ['RAW', 'SmackDown', 'NXT']:
                channel = self.bot.get_channel(config.discord['channel']['wwe'])
            elif 'AEW' in payload['name']:
                channel = self.bot.get_channel(config.discord['channel']['aew'])
            else:
                channel = self.bot.get_channel(config.discord['channel']['general'])
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
                await channel.send('@everyone', embed=embed)
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
    @commands.has_any_role(
        config.discord['role']['admin'], config.discord['role']['mod']
    )
    @checks.is_registered()
    async def scheduler_pending(self, ctx):
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
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Scheduler(bot))
