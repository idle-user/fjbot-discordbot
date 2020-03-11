"""This module provides basic checks to common procedures."""
import discord
from discord.ext import commands

from utils.fjclasses import DiscordUser, UserNotRegisteredError


def is_registered():
    """Check to see if the user is registered in database.

    :return: True if the :class:`utils.fjclasses.DiscordUser` exists.
    :raises: :class:`utils.fjclasses.UserNotRegisteredError` if User is not found in database.
    """

    async def predicate(ctx):
        """The inner call for :func:`utils.checks.is_registered`.

        :param ctx: The invocation context.
        :return: True if the :class:`utils.fjclasses.DiscordUser` exists.
        :raises: :class:`utils.fjclasses.UserNotRegisteredError` if User is not found in database.
        """
        if not DiscordUser(ctx.author).is_registered():
            raise UserNotRegisteredError('User not registered')
        return True

    return commands.check(predicate)


def confirm(author):
    """

    :param author: The `ctx.author` attribute value.
    :return: `True` if the author matches the context and properly responds, `False` otherwise.
    """

    def inner_check(ctx):
        """The inner call for :func:`utils.checks.confirm`.

        Checks whether the original author is responding to the query.

        :param ctx: The invocation context.
        :return: `True` if the author matches the context and properly responds, `False` otherwise.
        """
        return author == ctx.author and ctx.content.upper() in ['Y', 'N']

    return inner_check


def is_number(author):
    """

    :param author: The `ctx.author` attribute value.
    :return: `True` if the author matches the context and properly responds, `False` otherwise.
    """

    def inner_check(ctx):
        """The inner call for :func:`utils.checks.is_number`.

        Checks whether the original author is responding to the query.

        :param ctx: The invocation context.
        :return: `True` if the author matches the context and properly responds, `False` otherwise.
        """
        return author == ctx.author and ctx.content.isdigit()

    return inner_check


def is_dm(ctx):
    """Check to see if the message received is a direct message.

    :param ctx: The invocation context.
    :return: `True` if the context is a direct message, `False` otherwise.
    """
    return isinstance(ctx.channel, discord.DMChannel)
