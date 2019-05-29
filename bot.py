#!/usr/bin/env python3
import asyncio
import logging
import sys
import traceback
from datetime import datetime

import discord
from discord.ext import commands

import config
from utils import quickembed
from utils.fjclasses import (
    DbHelper,
    DiscordUser,
    GuildNotOriginError,
    UserNotRegisteredError,
)

logFormatter = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
logging.basicConfig(format=logFormatter, level=logging.INFO)
logger = logging.getLogger(__name__)

bot = discord.ext.commands.Bot(
    command_prefix=config.general['command_prefix'],
    description=config.general['description'],
)


def log(content=None, embed=None):
    bot.loop.create_task(discord_log(content=content, embed=embed))


def message_owner(content=None, embed=None):
    bot.loop.create_task(pm_owner(content=content, embed=embed))


async def discord_log(content=None, embed=None):
    await bot.wait_until_ready()
    channel_log = bot.get_channel(config.discord['channel']['log'])
    await channel_log.send(content=content, embed=embed)


async def pm_owner(content=None, embed=None):
    pass


@bot.event
async def on_command_error(ctx, error):
    msg = None
    if isinstance(error, commands.CommandNotFound):
        logger.error(
            'CommandNotFound: {0} - '
            '{1.guild.name}({1.guild.id}) - '
            '{1.author}'.format(error, ctx)
        )
        return
    if isinstance(error, commands.CommandOnCooldown):
        msg = 'Slow down! Try again in {:.1f} seconds.'.format(error.retry_after)
    elif isinstance(error, GuildNotOriginError):
        logger.error(
            'GuildNotOriginError: {0.command} - '
            '{0.guild.name}(0.guild.id) - '
            '{0.author}'.format(ctx)
        )
        return
    elif isinstance(error, UserNotRegisteredError):
        msg = (
            'Your Discord is not linked to an existing Matches account.\n'
            'Use `!register` or visit http://matches.fancyjesse.com to link '
            'to your existing account.'
        )
    elif isinstance(error, commands.CommandError):
        logger.error(
            'CommandError: {0} - '
            '{1.guild.name}({1.guild.id}) - '
            '{1.author} - {1.command}'.format(error, ctx)
        )
        return
    elif isinstance(error, commands.CommandInvokeError):
        if isinstance(error.original, asyncio.TimeoutError):
            msg = 'Took too long to confirm. Try again.'
    if msg:
        await ctx.send(embed=quickembed.error(desc=msg, user=DiscordUser(ctx.author)))
    else:
        raise error


@bot.event
async def on_message(ctx):
    if ctx.author.bot:
        return
    if not ctx.content.startswith(config.general['command_prefix']):
        return
    res = DbHelper().chatroom_command(ctx.content.split(' ')[0])
    if res['success']:
        await ctx.channel.send(res['message'].replace('@mention', ctx.author.mention))
        return
    tokens = ctx.content.split(' ')
    ctx.content = '{} {}'.format(tokens[0].lower(), ' '.join(tokens[1:]))
    await bot.process_commands(ctx)


@bot.event
async def on_ready():
    bot.start_dt = datetime.now()
    logger.info('START DiscordBot `{}`'.format(bot.user.name))


@bot.command(name='load', hidden=True)
@commands.is_owner()
async def cog_load(ctx, cog: str):
    try:
        cog = cog if 'cogs.' in cog else 'cogs.{}'.format(cog)
        bot.load_extension(cog)
        await ctx.send('```\n`{}` loaded\n```'.format(cog))
    except (AttributeError, ImportError) as e:
        await ctx.send('```py\n{}: {}\n```'.format(type(e).__name__, str(e)))


@bot.command(name='unload', hidden=True)
@commands.is_owner()
async def cog_unload(ctx, cog: str):
    try:
        cog = cog if 'cogs.' in cog else 'cogs.{}'.format(cog)
        bot.unload_extension(cog)
        await ctx.send('```\n`{}` unloaded\n```'.format(cog))
    except (AttributeError, ImportError) as e:
        await ctx.send('```py\n{}: {}\n```'.format(type(e).__name__, str(e)))


@bot.command(name='reload', hidden=True)
@commands.is_owner()
async def cog_reload(ctx, cog: str):
    try:
        cog = cog if 'cogs.' in cog else 'cogs.{}'.format(cog)
        bot.unload_extension(cog)
        bot.load_extension(cog)
        await ctx.send('```\n`{}` reloaded\n```'.format(cog))
    except (AttributeError, ImportError) as e:
        await ctx.send('```py\n{}: {}\n```'.format(type(e).__name__, str(e)))


if __name__ == '__main__':
    bot.log = log
    bot.message_owner = message_owner
    for extension in config.general['startup_cogs']:
        try:
            bot.load_extension(extension)
            logger.info('Loaded extension `{}`'.format(extension))
        except Exception:
            logger.error(f'Failed to load extension `{extension}`', file=sys.stderr)
            traceback.print_exc()
    bot.run(config.discord['access_token'])
    logger.info('END DiscordBot `{}`'.format(bot.user.name))
