import discord
from discord.ext import commands

from utils import checks, quickembed
from utils.fjclasses import DiscordUser


class FJBucks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='donate', hidden=True)
    @commands.is_owner()
    async def donate_bucks(self, ctx, amount: int, member: discord.Member):
        user = DiscordUser(ctx.author)
        recipient = DiscordUser(member)
        if not recipient.is_registered():
            embed = quickembed.error(
                desc='{} is not registered'.format(recipient.name), user=user
            )
        else:
            recipient.fjbucks_transaction(amount, 'owner authorized')
            embed = quickembed.success(
                desc='Donated **{} FJBucks** to {}'.format(amount, recipient.name),
                user=user,
            )
        await ctx.send(embed=embed)

    @commands.command(name='wallet', hidden=True)
    @checks.is_registered()
    async def fjbucks_balance(self, ctx):
        await ctx.send(embed=DiscordUser(ctx.author).fjbucks_wallet_embed())


def setup(bot):
    bot.add_cog(FJBucks(bot))
