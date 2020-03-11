"""This module provides a quick way to personalize messages back to the user.

Instead of flat text messages or going through all the steps to setup and personalize rich content, this module is used.
"""
import discord

color = {
    'None': 0x36393F,
    'red': 0xFF0000,
    'blue': 0x0080FF,
    'green': 0x80FF00,
    'white': 0xFFFFFF,
    'black': 0x000000,
    'orange': 0xFF8000,
    'yellow': 0xFFFF00,
}


def filler(embed, desc, user):
    """Creates the rich content and fills in all `user` info.

    :param embed: The base rich content.
    :param desc: The title of the rich content.
    :param user: The :class:`utils.fjclasses.DiscordUser` responding to.
    :return: The personalized rich content.
    """
    if user:
        if user.discord.bot:
            embed.set_author(name=desc, icon_url=user.discord.avatar_url)
        elif user.is_registered():
            embed.set_author(
                name='{0.discord.display_name} ({0.username})'.format(user),
                icon_url=user.discord.avatar_url,
                url=user.url,
            )
        else:
            embed.set_author(name=user.discord, icon_url=user.discord.avatar_url)
        embed.description = desc
    else:
        embed.set_author(name='Notification')

    embed.description = desc
    return embed


def general(desc, user=None):
    """Styles the rich content for a generic response. Colored blue.

    :param desc: The title of the rich content.
    :param user: The :class:`utils.fjclasses.DiscordUser` responding to.
    :return: The personalized rich content.
    """
    embed = discord.Embed(color=color['blue'])
    embed = filler(embed=embed, desc=desc, user=user)
    return embed


def info(desc, user=None):
    """Styles the rich content for a informative response. Colored white.

    :param desc: The title of the rich content.
    :param user: The :class:`utils.fjclasses.DiscordUser` responding to.
    :return: The personalized rich content.
    """
    embed = discord.Embed(color=color['white'])
    embed = filler(embed=embed, desc=desc, user=user)
    return embed


def error(desc, user=None):
    """Styles the rich content for a failed response. Colored red.

    :param desc: The title of the rich content.
    :param user: The :class:`utils.fjclasses.DiscordUser` responding to.
    :return: The personalized rich content.
    """
    embed = discord.Embed(color=color['red'])
    embed = filler(embed=embed, desc=desc, user=user)
    return embed


def success(desc, user=None):
    """Styles the rich content for a successful response. Colored green.

    :param desc: The title of the rich content.
    :param user: The :class:`utils.fjclasses.DiscordUser` responding to.
    :return: The personalized rich content.
    """
    embed = discord.Embed(color=color['green'])
    embed = filler(embed=embed, desc=desc, user=user)
    return embed


def question(desc, user=None):
    """Styles the rich content for a question response. Colored yellow.

    :param desc: The title of the rich content.
    :param user: The :class:`utils.fjclasses.DiscordUser` responding to.
    :return: The personalized rich content.
    """
    embed = discord.Embed(color=color['yellow'])
    embed = filler(embed=embed, desc=desc, user=user)
    return embed
