from datetime import datetime
import asyncio
import random

from discord.ext import commands
import discord

from utils.dbhandler import DBHandler
from utils import credentials


class Member:

	def __init__(self, bot):
		self.bot = bot
		self.dbhandler = DBHandler()
		
	@commands.command(name='commands', aliases=['misc'], pass_context=True)
	async def misc_commands(self, ctx):
		mcs = self.dbhandler.misc_commands()
		await self.bot.say('```Miscellaneous Commands:\n{}```'.format('\n'.join(mcs)))

	@commands.command(pass_context=True)
	async def report(self, ctx):
		owner = ctx.message.server.get_member(credentials.discord['owner_id'])
		if owner:
			await self.bot.send_message(owner, '```\nREPORT\n[#{0.channel}] {0.author}: {0.content}```'.format(ctx.message))
			await self.bot.say('`Report sent.`')
		
	@commands.command(pass_context=True)
	async def joined(self, member:discord.Member):
		await self.self.bot.say('`{0.name} joined in {0.joined_at}`'.format(member))
	
	@commands.command()
	async def invite(self):
		await self.bot.say(credentials.discord['invite_link'])

	@commands.command(name='role', aliases=['roles', 'toprole'], pass_context=True)
	async def member_roles(self, ctx):
		await self.bot.say('`Your Roles: {}`'.format([role.name for role in ctx.message.author.roles]).replace('@',''))

	@commands.command(name='uptime')
	async def bot_uptime(self):
		await self.bot.say('`Uptime: {}`'.format(datetime.now()-self.bot.start_dt))

	@commands.command(pass_context=True)
	async def countdown(self):
		n = 5
		while n > 0:
			await self.bot.say('**`{}`**'.format(n))
			await asyncio.sleep(1)
			n = n -1
		await self.bot.say('**`GO!`**')

	@commands.command(name='flip', aliases=['coin'])
	async def flip_coin(self):
		await self.bot.say('You flipped `{}`.'.format('Heads' if random.getrandbits(1) else 'Tails'))

	@commands.command(name='roll', aliases=['dice'])
	async def roll_dice(self):
		await self.bot.say('You rolled `{}` and `{}`.'.format(random.randint(1,6), random.randint(1,6)))

	@commands.command(name='slap', pass_context=True)
	async def slap_member(self, ctx, member:discord.Member=None, reason=None):
		if member:
			if member.bot:
				await self.bot.say("*{} slapped {}'s cheeks for trying to abuse a bot*".format(member.mention, ctx.message.author.mention))
		#if not ctx.invoked_subcommand:
			elif member == ctx.message.author:
				await self.bot.say('{}, you god damn masochist.'.format(member.mention))		
			else:
				await self.bot.say('*{} slapped {}{}*'.format(ctx.message.author.mention, member.mention, ' for {}'.format(reason) if reason else ''))
	
	#@slap_member.command(name'fjbot')
	#async def _slap_bot(self, member):
	#	await self.bot.say('slap.command subcommand')
			
	@commands.command(pass_context=True)
	async def tickle(self, ctx, member:discord.Member=None, reason=None):
		if member:
			if member.bot:
				await self.bot.say("*{} spread {}'s cheeks and tickled the inside for trying to touch bot*".format(member.mention, ctx.message.author.mention))
			elif member == ctx.message.author:
				await self.bot.say('{}, tickling yourself are you now? Pathetic..'.format(member.mention))		
			else:
				await self.bot.say('*{} tickled {}{}*'.format(ctx.message.author.mention, member.mention, ' for {}'.format(reason) if reason else ''))

	@commands.command(pass_context=True)
	async def mock(self, ctx, member:discord.Member=None):
		if member and member.bot: 
			await self.bot.say('No.')
			return
		async for msg in self.bot.logs_from(ctx.message.channel, limit=50):
			if msg.content.startswith('!') or '@' in msg.content: continue;
			if msg.author == member:
				mock_msg = ''.join([l.upper() if random.getrandbits(1) else l.lower() for l in msg.content])
				await self.bot.say('```"{}"\n    - {}```'.format(mock_msg, member))
				break
	
def setup(bot):
	bot.add_cog(Member(bot))
