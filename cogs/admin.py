"""This cog provides administrative commands to Discord users with elevated privileges."""
import discord
from discord.ext import commands

from utils import checks, quickembed
from utils.fjclasses import DiscordUser


class Admin(commands.Cog):
    """The Admin cog class."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='changeprefix', hidden=True)
    @commands.has_permissions(administrator=True)
    async def update_guild_prefix(self, ctx, prefix):
        """Updates the command prefix for the Discord server.

        .. Note::
            Requires `administrator` privilege.

        :param ctx: The invocation context.
        :param prefix: The command prefix to update to.
        """
        user = DiscordUser(ctx.author)
        if len(prefix) > 3:
            embed = quickembed.error(
                desc='Prefix can not be longer than 3 characters', user=user
            )
        else:
            user.update_guild_info(ctx.guild, prefix)
            stored_prefix = user.guild_info(ctx.guild.id)['prefix']
            if prefix == stored_prefix:
                embed = quickembed.success(
                    desc='Prefix updated to **{}**'.format(stored_prefix), user=user,
                )
            else:
                embed = quickembed.error(desc='Failed to update prefix', user=user)
        await ctx.send(embed=embed)

    @commands.command(name='clear', hidden=True)
    @commands.has_permissions(administrator=True)
    async def delete_messages(self, ctx, limit: int = 1):
        """Deletes the latest messages in the channel. The invoking message is deleted.

        .. Note::
            Requires `administrator` privilege.

        :param ctx: The invocation context.
        :param limit: The number of messages to delete. Default is 1.
        """
        await ctx.message.delete()
        await ctx.channel.purge(limit=limit)

    @commands.command(name='say', hidden=True)
    @commands.is_owner()
    async def repeat_message(self, ctx, *, msg: str):
        """Repeats the message as the bot. The invoking message is deleted.

        .. Note::
            Only the bot owner can use this.

        :param ctx: The invocation context.
        :param msg: The message the bot will repeat.
        """
        await ctx.message.delete()
        await ctx.send(msg)

    @commands.command(name='spam', hidden=True)
    @commands.has_permissions(manage_messages=True)
    @checks.is_registered()
    async def delete_spam_messages(self, ctx):
        """Deletes duplicate messages in the channel.

        .. Note::
            Messages are checked per author.
            The original message will remain.

        :param ctx: The invocation context.
        """
        msgs = []
        spam = []
        async for msg in ctx.channel.history(limit=50):
            c = str(msg.author) + msg.content
            if c in msgs:
                spam.append(msg)
            else:
                msgs.append(c)

        spam.append(ctx.message)
        await ctx.channel.delete_messages(spam)
        if len(spam) > 1:
            embed = quickembed.info(
                '```Deleted {} spam messages```'.format(len(spam)),
                DiscordUser(ctx.author),
            )
            self.bot.log(embed=embed)

    @commands.command(name='playing', hidden=True)
    @commands.is_owner()
    async def update_presence_playing(self, ctx, *, name=None):
        """Updates the bot's status to `playing`.

        .. Note::
            Only the bot owner can use this.

        :param ctx: The invocation context.
        :param name: The name of the activity.
        """
        activity = discord.Activity(type=discord.ActivityType.playing, name=name)
        await self.bot.change_presence(activity=activity)

    @commands.command(name='streaming', hidden=True)
    @commands.is_owner()
    async def update_presence_streaming(self, ctx, url: str = None, *, name=None):
        """Updates the bot's status to `streaming`.

        .. Note::
            Only the bot owner can use this.

        :param ctx: The invocation context.
        :param url: The URL to the stream.
        :param name: The name of the stream.
        """
        activity = discord.Activity(
            type=discord.ActivityType.streaming, name=name, url=url
        )
        await self.bot.change_presence(activity=activity)

    @commands.command(name='watching', hidden=True)
    @commands.is_owner()
    async def update_presence_watching(self, ctx, *, name=None):
        """Updates the bot's status to `watching`.

        .. Note::
            Only the bot owner can use this.

        :param ctx: The invocation context.
        :param name: The name of activity.
        """
        activity = discord.Activity(type=discord.ActivityType.watching, name=name)
        await self.bot.change_presence(activity=activity)

    @commands.command(name='listening', hidden=True)
    @commands.is_owner()
    async def update_presence_listening(self, ctx, *, name=None):
        """Updates the bot's status to `listening`.

        .. Note::
            Only the bot owner can use this.

        :param ctx: The invocation context.
        :param name: The name of activity.
        """
        activity = discord.Activity(type=discord.ActivityType.listening, name=name)
        await self.bot.change_presence(activity=activity)

    @commands.command(name='addcommand', hidden=True)
    @commands.is_owner()
    @checks.is_registered()
    async def add_discord_command(self, ctx, command, *, response):
        """Inserts a quick chatroom command.

        :param ctx: The invocation context.
        :param command: The command name to add.
        :param response: The response for the command.
        """
        user = DiscordUser(ctx.author)
        command = '!{}'.format(command.strip('!'))
        res = user.add_chatroom_command(command, response)
        if res['success']:
            embed = quickembed.success(
                desc='Command `{}` updated'.format(command), user=user
            )
        else:
            embed = quickembed.error(desc='Failed', user=user)
        await ctx.send(embed=embed)

    @commands.command(name='updatecommand', hidden=True)
    @commands.is_owner()
    @checks.is_registered()
    async def update_discord_command(self, ctx, command, *, response):
        """Updates a quick chatroom command.

        .. Note::
            Only the bot owner can use this.

        :param ctx: The invocation context.
        :param command: The command name to update.
        :param response: The updated response for the command.
        """
        user = DiscordUser(ctx.author)
        command = '!{}'.format(command.strip('!'))
        res = user.update_chatroom_command(command, response)
        if res['success']:
            embed = quickembed.success(
                desc='Command `{}` updated'.format(command), user=user
            )
        else:
            embed = quickembed.error(desc='Failed', user=user)
        await ctx.send(embed=embed)

    @commands.command(name='mute', hidden=True)
    @commands.has_permissions(manage_roles=True)
    @checks.is_registered()
    async def mute_member(self, ctx, member: discord.Member):
        """Mutes a member by assigning them the `Muted` role.

        .. Note::
            Requires `Manage Roles` privilege.

        .. Note::
            A `Muted` role must exist with the proper permissions.
            It's a simple role that can only read the channels and not send messages.

        :param ctx: The invocation context.
        :param member:
        """
        user = DiscordUser(ctx.author)
        role = discord.utils.find(lambda r: r.name == 'Muted', ctx.guild.roles)
        if not role:
            embed = quickembed.error(desc='`Muted` role does not exist', user=user)
        elif role not in member.roles:
            await member.add_roles(role)
            embed = quickembed.success(desc='Muted {}'.format(member), user=user)
        else:
            embed = quickembed.error(
                desc='{} is already muted'.format(member), user=user
            )
        await ctx.send(embed=embed)

    @commands.command(name='unmute', hidden=True)
    @commands.has_permissions(manage_roles=True)
    @checks.is_registered()
    async def unmute_member(self, ctx, member: discord.Member):
        """Unmutes a member by removing their `Muted` role.

        .. Note::
            Requires `Manage Roles` privilege.

        .. Note::
            A `Muted` role must exist with the proper permissions.
            It's a simple role that can only read the channels and not send messages.

        :param ctx: The invocation context.
        :param member:
        """
        user = DiscordUser(ctx.author)
        role = discord.utils.find(lambda r: r.name == 'Muted', ctx.guild.roles)
        if not role:
            embed = quickembed.error(desc='`Muted` role does not exist', user=user)
        elif role in member.roles:
            await member.remove_roles(role)
            embed = quickembed.success(desc='Unmuted {}'.format(member), user=user)
        else:
            embed = quickembed.error(
                desc='{} is already unmuted'.format(member), user=user
            )
        await ctx.send(embed=embed)


def setup(bot):
    """Required for cogs.

    :param bot: The Discord bot.
    """
    bot.add_cog(Admin(bot))
