from datetime import datetime
import asyncio
import random

from discord.ext import commands
import discord

from utils.fjclasses import DiscordUser
from utils import config, quickembed


class Member(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name='commands', aliases=['misc'])
	async def misc_commands(self, ctx):
		user = DiscordUser(ctx.author)
		rows = user.chatroom_command_list()
		msg = ''
		for row in rows:
			msg = msg + row['command'] + '\n'
			if len(msg) > 1000:
				msg = msg + '...'
				embed = quickembed.info(desc='Chat Commands', user=user)
				embed.add_field(name='\u200b', value=msg, inline=False)
				await ctx.send(embed=embed)
				msg = '...\n'
		embed = quickembed.info(desc='Chat Commands', user=user)
		embed.add_field(name='\u200b', value=msg, inline=False)
		await ctx.send(embed=embed)

	@commands.command()
	async def report(self, ctx, member:discord.Member, *, reason='no reason'):
		msg = '[#{}]\n{} reported {} for {}'.format(ctx.channel, ctx.author, member, reason)
		embed = quickembed.success(desc=msg, user=DiscordUser(ctx.author))
		self.bot.log('@here', embed=embed)
		await ctx.send(embed=embed)

	@commands.command()
	async def joined(self, ctx, member:discord.Member=None):
		member = member if member else ctx.author
		embed = quickembed.info(desc='{0.name} joined on `{0.joined_at}`'.format(member), user=DiscordUser(ctx.author))
		await ctx.send(embed=embed)

	@commands.command()
	async def invite(self, ctx):
		embed = quickembed.info(desc='Invite Link\n{}'.format(config.discord['invite_link']), user=DiscordUser(ctx.author))
		await ctx.send(embed=embed)

	@commands.command(name='role', aliases=['roles', 'toprole'])
	async def member_roles(self, ctx):
		roles = '{}'.format([role.name for role in ctx.author.roles])
		embed = quickembed.info(desc='Roles: {}'.format(roles), user=DiscordUser(ctx.author))
		await ctx.send(embed=embed)

	@commands.command(name='uptime')
	async def uptime(self, ctx):
		embed = quickembed.info(desc='Uptime: {}'.format(datetime.now()-self.bot.start_dt), user=DiscordUser(ctx.author))
		await ctx.send(embed=embed)

	@commands.command()
	async def countdown(self, ctx, *, startnum=5):
		startnum = 5 if startnum>10 else startnum
		user = DiscordUser(ctx.author)
		embed = quickembed.info(desc='Countdown', user=user)
		embed.add_field(name=startnum, value='\u200b', inline=False)
		msg = await ctx.send(embed=embed)
		await asyncio.sleep(1)
		for i in range(startnum-1, 0, -1):
			embed = quickembed.info(desc='countdown', user=user)
			embed.add_field(name=i, value='\u200b', inline=False)
			await msg.edit(embed=embed)
			await asyncio.sleep(1)
		embed = quickembed.info(desc='countdown', user=user)
		embed.add_field(name='GO!', value='\u200b', inline=False)
		await msg.edit(embed=embed)

	@commands.command(name='flip', aliases=['coin'])
	async def flip_coin(self, ctx):
		result = 'Heads' if random.getrandbits(1) else 'Tails'
		embed = quickembed.info(desc='Coin flip', user=DiscordUser(ctx.author))
		embed.add_field(name=result, value='\u200b', inline=False)
		await ctx.send(embed=embed)

	@commands.command(name='roll', aliases=['dice'])
	async def roll_dice(self, ctx):
		result = '[{}] [{}]'.format(random.randint(1,6), random.randint(1,6))
		embed = quickembed.info(desc='Dice roll', user=DiscordUser(ctx.author))
		embed.add_field(name=result, value='\u200b', inline=False)
		await ctx.send(embed=embed)

	@commands.command(name='slap')
	async def slap_member(self, ctx, member:discord.Member=None, *, reason='no reason'):
		user = DiscordUser(ctx.author)
		if not member:
			embed = quickembed.info("{} slapped the air. They're a different kind of special.".format(user.mention), user=user)
		elif member.bot:
			embed = quickembed.info("{} slapped {}'s cheeks for trying to abuse a bot".format(member.mention, user.mention), user=user)
		elif member == ctx.author:
			embed = quickembed.info('You god damn masochist', user=user)
		else:
			embed = quickembed.info('{} slapped {} for {}'.format(user.mention, member.mention, reason), user=user)
		await ctx.send(embed=embed)

	@commands.command(name='tickle')
	async def tickle_member(self, ctx, member:discord.Member=None, *, reason='no reason'):
		user = DiscordUser(ctx.author)
		if not member:
			embed = quickembed.info('{} tried to tickle someone, but everyone is ran away.'.format(user.mention), user=user)
		elif member.bot:
			embed = quickembed.info("{} spread {}'s cheeks and tickled the inside for trying to touch a bot".format(member.mention, user.mention), user=user)
		elif member == ctx.author:
			embed = quickembed.info('{} tickled themself. Pathetic..'.format(user.mention), user=user)
		else:
			embed = quickembed.info('{} tickled {} for {}'.format(user.mention, member.mention, reason), user=user)
		await ctx.send(embed=embed)

	@commands.command(name='hug')
	async def hug_member(self, ctx, member:discord.Member=None, *, reason='no reason'):
		user = DiscordUser(ctx.author)
		if not member:
			embed = quickembed.info('{} tried to hug someone, but no one was there.'.format(user.mention), user=user)
		elif member.bot:
			embed = quickembed.info("{} tried to hug a {}, but is rejected. Even bots doesn't like you.".format(user.mention, member.mention), user=user)
		elif member == ctx.author:
			embed = quickembed.info('{} hugged themself. Pathetic..'.format(user.mention), user=user)
		else:
			embed = quickembed.info('{} hugged {} for {}'.format(user.mention, member.mention, reason), user=user)
		await ctx.send(embed=embed)

	@commands.command(name='mock')
	async def mock_member(self, ctx, member:discord.Member=None):
		user = DiscordUser(ctx.author)
		if not member or member.bot:
			return
		async for m in ctx.channel.history(limit=50):
			if m.author == member and not m.content.startswith('!'):
				mock_msg = ''.join([l.upper() if random.getrandbits(1) else l.lower() for l in m.content])
				embed = quickembed.info('```"{}"\n    - {}```'.format(mock_msg, member), user=user)
				await ctx.send(embed=embed)
				break

def setup(bot):
	bot.add_cog(Member(bot))
