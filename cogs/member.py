from datetime import datetime
import asyncio
import random

from discord.ext import commands
import discord

from utils.dbhandler import DBHandler
from utils import credentials, quickembed


class Member(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		self.dbhandler = DBHandler()

	@commands.command(name='commands', aliases=['misc'])
	async def misc_commands(self, ctx):
		mcs = self.dbhandler.misc_commands()
		msg = 'Matches Commands\n------------'
		for mc in mcs:
			temp_msg = msg + '\n' + mc
			if len(temp_msg) > 1900:
				await ctx.author.send('```{}```'.format(msg))
				msg = '...\n'
			else:
				msg = temp_msg
		await ctx.author.send('```{}```'.format(msg))

	@commands.command()
	async def report(self, ctx):
		await ctx.message.delete()
		msg = '@here\n``` REPORT\n[#{0.channel}] {0.author}: {0.message.content} ```'.format(ctx)
		self.bot.log(msg)
		await ctx.author.send('``` Report sent. ```')

	@commands.command()
	async def joined(self, member:discord.Member):
		await self.ctx.send('`{0.name} joined in {0.joined_at}`'.format(member))

	@commands.command()
	async def invite(self, ctx):
		await ctx.send(credentials.discord['invite_link'])

	@commands.command(name='role', aliases=['roles', 'toprole'])
	async def member_roles(self, ctx):
		await ctx.send('`Your Roles: {}`'.format([role.name for role in ctx.author.roles]).replace('@',''))

	@commands.command(name='uptime')
	async def uptime(self, ctx):
		await ctx.send('`Uptime: {}`'.format(datetime.now()-self.bot.start_dt))

	@commands.command()
	async def countdown(self, ctx):
		#e = quickembed.general(author=ctx.author, desc='countdown')
		n = 5
		while n > 0:
			await ctx.send('**`{}`**'.format(n))
			await asyncio.sleep(1)
			n = n -1
		await ctx.send('**`GO!`**')

	@commands.command(name='flip', aliases=['coin'])
	async def flip_coin(self, ctx):
		await ctx.send('You flipped `{}`.'.format('Heads' if random.getrandbits(1) else 'Tails'))

	@commands.command(name='roll', aliases=['dice'])
	async def roll_dice(self, ctx):
		await ctx.send('You rolled `{}` and `{}`.'.format(random.randint(1,6), random.randint(1,6)))

	@commands.command(name='slap')
	async def slap_member(self, ctx, member:discord.Member=None, *,reason=None):
		await ctx.message.delete()
		if member:
			if member.bot:
				await ctx.send("*{} slapped {}'s cheeks for trying to abuse a bot*".format(member.mention, ctx.author.mention))
		#if not ctx.invoked_subcommand:
			elif member == ctx.author:
				await ctx.send('{}, you god damn masochist.'.format(member.mention))
			else:
				await ctx.send('*{} slapped {}{}*'.format(ctx.author.mention, member.mention, ' for {}'.format(reason) if reason else ''))

	@commands.command()
	async def tickle(self, ctx, member:discord.Member=None, *, reason=None):
		await ctx.message.delete()
		if member:
			if member.bot:
				await ctx.send("*{} spread {}'s cheeks and tickled the inside for trying to touch bot*".format(member.mention, ctx.author.mention))
			elif member == ctx.author:
				await ctx.send('{}, tickling yourself are you now? Pathetic..'.format(member.mention))
			else:
				await ctx.send('*{} tickled {}{}*'.format(ctx.author.mention, member.mention, ' for {}'.format(reason) if reason else ''))

	@commands.command()
	async def mock(self, ctx, member:discord.Member=None):
		if member and member.bot:
			await ctx.send('No.')
			return
		async for msg in ctx.channel.history(limit=50):
			if msg.content.startswith('!') or '@' in msg.content: continue;
			if msg.author == member:
				mock_msg = ''.join([l.upper() if random.getrandbits(1) else l.lower() for l in msg.content])
				await ctx.send('```"{}"\n    - {}```'.format(mock_msg, member))
				break

def setup(bot):
	bot.add_cog(Member(bot))
