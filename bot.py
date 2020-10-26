#!/usr/bin/env python3
"""The main module that runs the bot.

Contains owner commands to load and unload cogs, basic logging, and command prefix checks.
"""
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

if config.logging['debug']:
    logging.basicConfig(format=config.logging['format'], level=logging.DEBUG)
else:
    logging.basicConfig(format=config.logging['format'], level=logging.INFO)
logger = logging.getLogger(__name__)


def prefix(bot, ctx):
    """Returns the command prefix defined by a guild from database.

     If it does not exist, it inserts record with default command prefix defined in :mod:`config`.

    :param bot: The Discord Bot.
    :param ctx: The invocation context.
    :return: The guild's command prefix.
    """
    if not ctx.guild:
        return config.base['default_prefix']
    guild_info = DbHelper().guild_info(ctx.guild.id)
    if not guild_info:
        logger.info('No record found for guild: {0.name}({0.id})'.format(ctx.guild))
        DbHelper().update_guild_info(ctx.guild, config.base['default_prefix'])
        guild_info = DbHelper().guild_info(ctx.guild.id)
    return guild_info['prefix']


bot = discord.ext.commands.Bot(
    command_prefix=prefix, description=config.base['description'],
)
bot.remove_command("help")


def log(content=None, embed=None):
    """The non-async version of :func:`bot.discord_log`.

    :param content: The plain text to send.
    :param embed: The rich embed for the content to send.
    """
    bot.loop.create_task(discord_log(content=content, embed=embed))


def message_owner(content=None, embed=None):
    """The non-async version of :func:`bot.pm_owner`.

    :param content: The plain text to send.
    :param embed: The rich embed for the content to send.
    """
    bot.loop.create_task(pm_owner(content=content, embed=embed))


async def discord_log(content=None, embed=None):
    """Sends message to log channel defined in :mod:`config`.

    :param content: The plain text to send.
    :param embed: The rich embed for the content to send.
    """
    await bot.wait_until_ready()
    channel_log = bot.get_channel(config.base['channel']['log'])
    await channel_log.send(content=content, embed=embed)


async def pm_owner(content=None, embed=None):
    """Sends private message to owner defined in :mod:`config`.

    :param content: The plain text to send.
    :param embed: The rich embed for the content to send.
    """
    pass


@bot.event
async def on_command_error(ctx, error):
    """Called when an error through a command occurs. Common instances are handled appropriately.

    If error is not handled, the error is raised.

    :param ctx: The invocation context.
    :param error: The command error.
    """
    msg = None
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.CommandOnCooldown):
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
            'Use `!register` or visit http://idleuser.com/projects/matches to link '
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


'''
@bot.event
async def on_message(ctx):
    """Called whenever a message is sent to a server the bot is watching.

    The message is first checked to see if a :func:`bot.prefix` is used.
    If it is, it will check the :func:`utils.fjclasses.chatroom_command` for the proper response.
    If no response is found, :func:`process_command` is called.

    :param ctx: The invocation context.
    """
    if ctx.author.bot:
        return
    if not ctx.content.startswith(prefix(bot, ctx)):
        return
    res = DbHelper().chatroom_command(ctx.content.split(' ')[0])
    if res['success']:
        await ctx.channel.send(res['message'].replace('@mention', ctx.author.mention))
    else:
        tokens = ctx.content.split(' ')
        ctx.content = '{} {}'.format(tokens[0].lower(), ' '.join(tokens[1:]))
        await bot.process_commands(ctx)
'''


@bot.event
async def on_ready():
    """Called when the client is done preparing the data received from Discord.

        Stores the datetime the bot started as an attribute.
    """
    bot.start_dt = datetime.now()
    logger.info(
        'START bot `{0.name} - {0.id}` Discord Version: {1}'.format(
            bot.user, discord.__version__
        )
    )


@bot.command(name='load', hidden=True)
@commands.is_owner()
async def cog_load(ctx, cog: str):
    """Loads the cog by name.

    The cog must be in cogs directory.

    :param ctx: The invocation context.
    :param cog: The name of the cog.
    """
    try:
        cog = cog if 'cogs.' in cog else 'cogs.{}'.format(cog)
        bot.load_extension(cog)
        await ctx.send('```\n`{}` loaded\n```'.format(cog))
    except (AttributeError, ImportError) as e:
        await ctx.send('```py\n{}: {}\n```'.format(type(e).__name__, str(e)))


@bot.command(name='unload', hidden=True)
@commands.is_owner()
async def cog_unload(ctx, cog: str):
    """Unload the cog by name.

    :param ctx: The invocation context.
    :param cog: The name of the cog.
    """
    try:
        cog = cog if 'cogs.' in cog else 'cogs.{}'.format(cog)
        bot.unload_extension(cog)
        await ctx.send('```\n`{}` unloaded\n```'.format(cog))
    except (AttributeError, ImportError) as e:
        await ctx.send('```py\n{}: {}\n```'.format(type(e).__name__, str(e)))


@bot.command(name='reload', hidden=True)
@commands.is_owner()
async def cog_reload(ctx, cog: str):
    """Unloads and loads the cog by name.

    The cog must be in the cogs directory.

    :param ctx: The invocation context.
    :param cog: The name of the cog.
    """
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
    for extension in config.base['startup_cogs']:
        try:
            bot.load_extension(extension)
            logger.info('Loaded extension `{}`'.format(extension))
        except Exception as e:
            logger.debug('Failed to load extension: {}'.format(e))
            logger.error(f'Failed to load extension `{extension}`', file=sys.stderr)
            traceback.print_exc()
    bot.run(config.discord['access_token'])
    logger.info('END bot `{0.name} - {0.id}`'.format(bot.user.name))
