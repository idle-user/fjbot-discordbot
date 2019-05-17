import discord
from discord.ext import commands

import config
from utils import checks, quickembed
from utils.fjclasses import DiscordUser


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='clear', hidden=True)
    @commands.is_owner()
    async def delete_messages(self, ctx, limit: int = 1):
        await ctx.message.delete()
        await ctx.channel.purge(limit=limit)

    @commands.command(name='say', hidden=True)
    @commands.is_owner()
    async def repeat_message(self, ctx, *, msg: str):
        await ctx.message.delete()
        await ctx.send(msg)

    @commands.command(name='spam', hidden=True)
    @commands.has_any_role(
        config.discord['role']['admin'], config.discord['role']['mod']
    )
    @checks.is_registered()
    async def delete_spam_messages(self, ctx):
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
        activity = discord.Activity(type=discord.ActivityType.playing, name=name)
        await self.bot.change_presence(activity=activity)

    @commands.command(name='streaming', hidden=True)
    @commands.is_owner()
    async def update_presence_streaming(self, ctx, url: str = None, *, name=None):
        activity = discord.Activity(
            type=discord.ActivityType.streaming, name=name, url=url
        )
        await self.bot.change_presence(activity=activity)

    @commands.command(name='watching', hidden=True)
    @commands.is_owner()
    async def update_presence_watching(self, ctx, *, name=None):
        activity = discord.Activity(type=discord.ActivityType.watching, name=name)
        await self.bot.change_presence(activity=activity)

    @commands.command(name='listening', hidden=True)
    @commands.is_owner()
    async def update_presence_listening(self, ctx, *, name=None):
        activity = discord.Activity(type=discord.ActivityType.listening, name=name)
        await self.bot.change_presence(activity=activity)

    @commands.command(name='addcommand', hidden=True)
    @commands.has_role('Admin')
    @checks.is_registered()
    async def add_discord_command(self, ctx, command, *, response):
        user = DiscordUser(ctx.author)
        command = '!{}'.format(command.strip('!'))
        res = user.add_chatroom_command(command, response)
        if res['success']:
            embed = quickembed.success(
                desc='Command `{}` updated'.format(command), user=user
            )
        else:
            embed = quickembed.error(desc='Failed', user=user)
            await ctx.send('Failed')
        ctx.send(embed=embed)

    @commands.command(name='updatecommand', hidden=True)
    @commands.has_role('Admin')
    @checks.is_registered()
    async def update_discord_command(self, ctx, command, *, response):
        user = DiscordUser(ctx.author)
        command = '!{}'.format(command.strip('!'))
        res = user.update_chatroom_command(command, response)
        if res['success']:
            embed = quickembed.success(
                desc='Command `{}` updated'.format(command), user=user
            )
        else:
            embed = quickembed.error(desc='Failed', user=user)
            await ctx.send('Failed')
        ctx.send(embed=embed)

    @commands.command(name='mute', hidden=True)
    @commands.has_role('Admin')
    @checks.is_registered()
    async def mute_member(self, ctx, member: discord.Member):
        user = DiscordUser(ctx.author)
        role = discord.utils.find(lambda r: r.name == 'Muted', ctx.guild.roles)
        if not role:
            embed = quickembed.error(
                desc='`Muted` role does not exist'.format(ctx.author), user=user
            )
        elif role not in member.roles:
            await member.add_roles(role)
            embed = quickembed.success(desc='Muted {}'.format(ctx.author), user=user)
        else:
            embed = quickembed.error(
                desc='{} is already muted'.format(ctx.author), user=user
            )
        await ctx.send(embed=embed)

    @commands.command(name='unmute', hidden=True)
    @commands.has_role('Admin')
    @checks.is_registered()
    async def unmute_member(self, ctx, member: discord.Member):
        user = DiscordUser(ctx.author)
        role = discord.utils.find(lambda r: r.name == 'Muted', ctx.guild.roles)
        if not role:
            embed = quickembed.error(
                desc='`Muted` role does not exist'.format(ctx.author), user=user
            )
        elif role in member.roles:
            await member.remove_roles(role)
            embed = quickembed.success(desc='Unmuted {}'.format(ctx.author), user=user)
        else:
            embed = quickembed.error(
                desc='{} is already unmuted'.format(ctx.author), user=user
            )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Admin(bot))
