"""This cog provides basic bot interactions to Discord members."""
import asyncio
import logging
import random
from datetime import datetime

import discord
from discord.ext import commands

import config
from utils import checks, quickembed
from utils.fjclasses import DiscordUser

logger = logging.getLogger(__name__)


class Member(commands.Cog):
    """The Member class for the cog."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='id')
    async def send_discord_id(self, ctx):
        """Sends the user's Discord id through DM.

        This is useful for users that join through the website and have not linked their Discord accounts to their
        profile. After logging in to the website, their profile has a Discord ID field that they can fill. Once the
        value is set, the account is linked.

        :param ctx: The invocation context.
        """
        user = DiscordUser(ctx.author)
        msg = (
            'Your discord_id is: `{}`\n'
            'Link it to your http://matches.fancyjesse.com profile.'.format(
                user.discord.id
            )
        )
        embed = quickembed.general(desc=msg, user=user)
        await ctx.author.send(embed=embed)
        await ctx.send(embed=quickembed.general(desc='Information DMed', user=user))

    @commands.command(name='register', aliases=['verify'])
    async def register_user(self, ctx):
        """Registers the Discord user and provides a response.

        If the user is already registered, they will be notified. Otherwise, a confirmation request is created before
        registering the account. The user will have 15 seconds to respond with a `[Y/N]`. If `[Y]`, the account will
        attempt to register, the response is then delivered. If `[N]`, the request is cancelled.

        :param ctx: The invocation context.
        """
        embed = None
        user = DiscordUser(ctx.author)
        if user.is_registered():
            embed = quickembed.success(
                desc='Your Discord is already registered', user=user
            )
        else:
            text_question = (
                '[Y/N]\nYour Discord is not linked to an existing '
                'Matches account (http://matches.fancyjesse.com)\n'
                'Would you like to register a new account?'
            )
            embed_question = quickembed.question(user=user, desc=text_question)
            await ctx.send(embed=embed_question)
            confirm = await self.bot.wait_for(
                'message', check=checks.confirm(ctx.author), timeout=15.0
            )
            confirm.content = confirm.content.upper()
            if confirm.content == 'Y':
                response = user.register()
                if response['success']:
                    user.refresh()
                    embed = quickembed.success(desc=response['message'], user=user)
                    logger.info('`{}` registered'.format(user.username))
                else:
                    embed = quickembed.error(desc=response['message'], user=user)
                    logger.warning(
                        '`{}` failed to register - {}'.format(
                            user.username, response['message']
                        )
                    )
            elif confirm.content == 'N':
                embed = quickembed.error(
                    user=user, desc='Account registration cancelled'
                )
        if embed:
            await ctx.send(embed=embed)

    @commands.command(name='login')
    @checks.is_registered()
    async def user_login_link(self, ctx):
        """Sends a quick login link for the website to the user through DM.

        .. note::
            This bypasses the website login by using a temporary token. The token expires once the link is used or
            5 minutes has passed.

        :param ctx: The invocation context.
        """
        user = DiscordUser(ctx.author)
        link = user.request_login_link()
        msg = 'Quick login link for you! (link expires in 5 minutes)\n<{}>'.format(link)
        await ctx.author.send(embed=quickembed.general(desc=msg, user=user))
        embed = quickembed.success(user=user, desc='Login link DMed')
        await ctx.send(embed=embed)

    @commands.command(
        name='reset-pw', alias=['password-reset, password-reset, pw-reset']
    )
    @checks.is_registered()
    async def user_reset_password_link(self, ctx):
        """Sends a reset password link for the website to the user through DM.

        .. note::
            This bypasses the login credentials by using a temporary password. The temporary password is only valid for
            resetting the account's password. It expires once the password has changed or 5 minutes has passed.

        :param ctx: The invocation context.
        """
        user = DiscordUser(ctx.author)
        link = user.request_reset_password_link()
        msg = '<{}>\n(link expires in 5 minutes)'.format(link)
        await ctx.author.send(embed=quickembed.general(desc=msg, user=user))
        embed = quickembed.success(user=user, desc='Link DMed')
        await ctx.send(embed=embed)

    @commands.command(name='commands', aliases=['misc', 'command-list'])
    @commands.cooldown(1, 30.0, commands.BucketType.user)
    async def misc_commands(self, ctx):
        """Sends a link to the list of available *dumb commands*.

        :param ctx: The invocation context.
        """
        user = DiscordUser(ctx.author)
        embed = quickembed.info(
            desc='FJBot Command:\nhttps://fancyjesse.com/projects/fjbot/command-list',
            user=DiscordUser(ctx.author),
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 300.0, commands.BucketType.user)
    @checks.is_registered()
    async def report(self, ctx, member: discord.Member, *, reason='no reason provided'):
        """Reports another user to the bot owner.

        This sends an alert to the bot owner through a log channel defined in :mod:`config`.

        .. note::
            This should be used sparingly. If the Discord server has a lot of users, this may get annoying.

        :param ctx: The invocation context.
        :param member: The Discord user being reported.
        :param reason: The reason for reporting the Discord user.
        """
        msg = '[#{}]\n{} reported {}\nReason: {}'.format(
            ctx.channel, ctx.author, member, reason
        )
        embed = quickembed.success(desc=msg, user=DiscordUser(ctx.author))
        self.bot.log('@here', embed=embed)
        await ctx.send(embed=embed)

    @commands.command()
    async def joined(self, ctx, member: discord.Member = None):
        """Displays the date the user joined the Discord server.

        :param ctx: The invocation context.
        :param member: The Discord user to display.
        """
        member = member if member else ctx.author
        embed = quickembed.info(
            desc='{0.name} joined on `{0.joined_at}`'.format(member),
            user=DiscordUser(ctx.author),
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx):
        """Sends the Discord server invite link defined in :mod:`config`.

        :param ctx: The invocation context.
        """
        embed = quickembed.info(
            desc='Invite Link:\n{}\n\nInvite Bot:\n{}'.format(
                config.base['invite']['guild'], config.base['invite']['bot']
            ),
            user=DiscordUser(ctx.author),
        )
        await ctx.send(embed=embed)

    @commands.command(name='roles', aliases=['my-roles'])
    async def member_roles(self, ctx):
        """Displays the roles the requesting user currently has in the server.

        :param ctx: The invocation context.
        """
        roles = '{}'.format([role.name for role in ctx.author.roles])
        embed = quickembed.info(
            desc='Roles: {}'.format(roles), user=DiscordUser(ctx.author)
        )
        await ctx.send(embed=embed)

    @commands.command(name='uptime')
    async def uptime(self, ctx):
        """Display the amount of time the bot has been alive.

        :param ctx: The invocation context.
        """
        embed = quickembed.info(
            desc='Uptime: {}'.format(datetime.now() - self.bot.start_dt),
            user=DiscordUser(ctx.author),
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def countdown(self, ctx, *, start_num=5):
        """Starts a basic countdown message.

         .. note::
            The original message is updated to avoid spamming the chat.

        :param ctx: The invocation context.
        :param start_num: The number to start countdown at. Must be 10 or below. Default is 5.
        """
        start_num = 5 if start_num > 10 else start_num
        user = DiscordUser(ctx.author)
        embed = quickembed.info(desc='Countdown', user=user)
        embed.add_field(name=start_num, value='\u200b', inline=False)
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(1)
        for i in range(start_num - 1, 0, -1):
            embed = quickembed.info(desc='countdown', user=user)
            embed.add_field(name=i, value='\u200b', inline=False)
            await msg.edit(embed=embed)
            await asyncio.sleep(1)
        embed = quickembed.info(desc='countdown', user=user)
        embed.add_field(name='GO!', value='\u200b', inline=False)
        await msg.edit(embed=embed)

    @commands.command(name='flip', aliases=['coin', 'coin-flip', 'flip-coin'])
    async def flip_coin(self, ctx):
        """Performs a basic coin flip and displays the result.

        :param ctx: The invocation context.
        """
        result = 'Heads' if random.getrandbits(1) else 'Tails'
        embed = quickembed.info(desc='Coin flip', user=DiscordUser(ctx.author))
        embed.add_field(name=result, value='\u200b', inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='roll', aliases=['dice', 'd6'])
    async def roll_dice(self, ctx):
        """Performs a basic dice roll and returns the result.

        :param ctx: The invocation context.
        """
        result = '[{}] [{}]'.format(random.randint(1, 6), random.randint(1, 6))
        embed = quickembed.info(desc='Dice roll', user=DiscordUser(ctx.author))
        embed.add_field(name=result, value='\u200b', inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='mock')
    async def mock_member(self, ctx, member: discord.Member = None):
        """Spongebob mocking memes a Discord users last message.

        .. note::
            The user being mocked must have a message within the last 50 messages in the channel that is not a command.
            Otherwise, nothing will happen.

            You cannot mock non-Discord user or a bot.

        :param ctx: The invocation context.
        :param member: The Discord user to mock.
        """
        user = DiscordUser(ctx.author)
        if member and not member.bot:
            async for m in ctx.channel.history(limit=50):
                if m.author == member and not m.content.startswith('!'):
                    mock_msg_list = []
                    alpha_cnt = 0
                    for letter in m.content:
                        if not letter.isalpha():
                            mock_msg_list.append(letter)
                            continue
                        alpha_cnt += 1
                        if alpha_cnt % 2:
                            mock_msg_list.append(letter.upper())
                        else:
                            mock_msg_list.append(letter.lower())
                    mock_msg = ''.join(mock_msg_list)
                    embed = quickembed.info(
                        '```"{}"\n    - {}```'.format(mock_msg, member), user=user
                    )
                    await ctx.send(embed=embed)
                    break

    @commands.command(name='slap')
    async def slap_member(
        self, ctx, member: discord.Member = None, *, reason='no reason provided'
    ):
        """Slap another Discord user.

        .. note::
            DO NOT ATTEMPT TO SLAP THE BOT.

        :param ctx: The invocation context.
        :param member: The Discord user to slap.
        :param reason: The reason for the slap.
        """
        user = DiscordUser(ctx.author)
        if not member:
            embed = quickembed.info(
                "{} slapped the air. They're a different kind of special.".format(
                    user.mention
                ),
                user=user,
            )
        elif member.bot:
            embed = quickembed.info(
                "{} slapped {}'s cheeks for trying to abuse a bot".format(
                    member.mention, user.mention
                ),
                user=user,
            )
        elif member == ctx.author:
            embed = quickembed.info('You god damn masochist', user=user)
        else:
            embed = quickembed.info(
                '{} slapped {}\nReason: {}'.format(
                    user.mention, member.mention, reason
                ),
                user=user,
            )
        await ctx.send(embed=embed)

    @commands.command(name='tickle')
    async def tickle_member(
        self, ctx, member: discord.Member = None, *, reason='no reason provided'
    ):
        """Tickle another Discord user.

        :param ctx: The invocation context.
        :param member: The Discord user to tickle.
        :param reason: The reason for the tickle.
        """
        user = DiscordUser(ctx.author)
        if not member:
            embed = quickembed.info(
                '{} tried to tickle someone, but everyone is ran away.'.format(
                    user.mention
                ),
                user=user,
            )
        elif member.bot:
            embed = quickembed.info(
                "{} spread {}'s cheeks and tickled the inside for trying to touch a bot".format(
                    member.mention, user.mention
                ),
                user=user,
            )
        elif member == ctx.author:
            embed = quickembed.info(
                '{} tickled themself. Pathetic..'.format(user.mention), user=user
            )
        else:
            embed = quickembed.info(
                '{} tickled {}\nReason: {}'.format(
                    user.mention, member.mention, reason
                ),
                user=user,
            )
        await ctx.send(embed=embed)

    @commands.command(name='hug')
    async def hug_member(
        self, ctx, member: discord.Member = None, *, reason='no reason provided'
    ):
        """Hug another Discord user.

        :param ctx: The invocation context.
        :param member: The Discord user to hug.
        :param reason: The reason for the hug.
        """
        user = DiscordUser(ctx.author)
        if not member:
            embed = quickembed.info(
                '{} tried to hug someone, but no one was there.'.format(user.mention),
                user=user,
            )
        elif member.bot:
            embed = quickembed.info(
                "{} tried to hug a {}, but is rejected. Even bots doesn't like you.".format(
                    user.mention, member.mention
                ),
                user=user,
            )
        elif member == ctx.author:
            embed = quickembed.info(
                '{} hugged themself. Pathetic..'.format(user.mention), user=user
            )
        else:
            embed = quickembed.info(
                '{} hugged {}\nReason: {}'.format(user.mention, member.mention, reason),
                user=user,
            )
        await ctx.send(embed=embed)

    @commands.command(name='punch')
    async def punch_member(
        self, ctx, member: discord.Member = None, *, reason='no reason provided'
    ):
        """Punch another Discord user.

        :param ctx: The invocation context.
        :param member: The Discord user to punch.
        :param reason: The reason for the punch.
        """
        user = DiscordUser(ctx.author)
        if not member:
            embed = quickembed.info(
                '{} tried to hug someone, but no one was there.'.format(user.mention),
                user=user,
            )
        elif member.bot:
            embed = quickembed.info(
                "{} tried to punch a {}, but hurt their hand instead.".format(
                    user.mention, member.mention
                ),
                user=user,
            )
        elif member == ctx.author:
            embed = quickembed.info(
                '{} punched themself. Idiot.'.format(user.mention), user=user
            )
        else:
            embed = quickembed.info(
                '{} punched {}\nReason: {}'.format(
                    user.mention, member.mention, reason
                ),
                user=user,
            )
        await ctx.send(embed=embed)


def setup(bot):
    """Required for cogs.

    :param bot: The Discord bot.
    """
    bot.add_cog(Member(bot))
