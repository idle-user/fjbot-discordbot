#!/usr/bin/env python3
from datetime import datetime
import sys, traceback
import asyncio

import discord

from utils.dbhandler import DBHandler
from utils import credentials, checks

startup_extensions = [
	'cogs.admin',
	'cogs.member',
	'cogs.matches',
	'cogs.twitter',
	'cogs.chatango',
	'cogs.voice',
]
description='FJBot is a Discord Bot written in Python by FancyJesse'
bot = discord.ext.commands.Bot(command_prefix='!', description=description)

def log(content=None, embed=None):
	bot.loop.create_task(discord_log(content=content, embed=embed))

def message_owner(content=None, embed=None):
	bot.loop.create_task(pm_owner(content=content, embed=embed))

async def discord_log(content=None, embed=None):
	await bot.wait_until_ready()
	channel_log = bot.get_channel(credentials.discord['channel']['log'])
	if content and '```' not in content:
		content = '```{}```'.format(content)
	await channel_log.send(content=content, embed=embed)

async def pm_owner(content=None, embed=None):
	server = bot.get_server(credentials.discord['server_id'])
	owner = server.get_member(credentials.discord['owner_id'])
	if owner:
		await bot.send_message(owner, content=content, embed=message)

@bot.event
async def on_message(ctx):
	if ctx.author.bot or not ctx.content.startswith('!'):
		return
	res = bot.dbhandler.discord_command(ctx.content.split(' ')[0])
	if res:
		''' 
		import random
		aprilfools = [
			'http://pm1.narvii.com/5941/318a80ae9a42d3ceeed60ef89fc58cf49b1c2a5f_00.jpg'
			,'http://sportsherniablog.com/wp-content/uploads/2015/06/Vince-scooter.jpg'
			,'https://uproxx.files.wordpress.com/2016/01/vince-mcmahon-most-muscular.jpg?quality=100&w=650'
			,'https://i.pinimg.com/originals/2b/20/a2/2b20a2b1bf65496251d05a19e7ac707a.jpg'
			,'https://i.gifer.com/UUmL.gif'
			,'https://i.imgflip.com/wu22l.jpg'
			,'lol you gay @mention. @everyone, make fun of him'
			,'ayyyyyyyy lol'
			,'sorry, wut?'
			,'fuk ur command @mention. Mah boi roman winning it all!!!!!!!!!!11111!!!!'
			,'https://vignette.wikia.nocookie.net/wrestling-is-fun/images/3/32/Vince-McMahon.jpg/revision/latest?cb=20140122103143'
			,'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRO_VdYeBtNMaK5GeK5nqNzG9Y4mDFUPKgdH3X6C-K65ARvbC9wHQ'
			,'https://media1.tenor.com/images/6e8987d8c9c0a5fa8a01b3a6443b6ea5/tenor.gif?itemid=11327475'
		]
		res['response'] = random.choice(aprilfools)
		'''
		await ctx.channel.send(res['response'].replace('@mention', ctx.author.mention))
		bot.dbhandler.discord_command_cnt(res['id'])
	else:
		tokens = ctx.content.split(' ')
		ctx.content = '{} {}'.format(tokens[0].lower(), ' '.join(tokens[1:]))
		await bot.process_commands(ctx)

@bot.event
async def on_ready():
	bot.start_dt = datetime.now()
	bot.log('[{}] Discord {}: START'.format(bot.start_dt, bot.user.name))

@bot.command(name='load', hidden=True)
@checks.is_owner()
async def cog_load(ctx, cog:str):
	try:
		cog = cog if 'cogs.' in cog else 'cogs.{}'.format(cog)
		bot.load_extension(cog)
		await ctx.send('```{} loaded```'.format(cog))
	except (AttributeError, ImportError) as e:
		await ctx.send('```py\n{}: {}\n```'.format(type(e).__name__, str(e)))

@bot.command(name='unload', hidden=True)
@checks.is_owner()
async def cog_unload(ctx, cog:str):
	try:
		cog = cog if 'cogs.' in cog else 'cogs.{}'.format(cog)
		bot.unload_extension(cog)
		await ctx.send('```{} unloaded```'.format(cog))
	except (AttributeError, ImportError) as e:
		await ctx.send('```py\n{}: {}\n```'.format(type(e).__name__, str(e)))

@bot.command(name='reload', hidden=True)
@checks.is_owner()
async def cog_reload(ctx, cog:str):
	try:
		cog = cog if 'cogs.' in cog else 'cogs.{}'.format(cog)
		bot.unload_extension(cog)
		bot.load_extension(cog)
		await ctx.send('```{} reloaded```'.format(cog))
	except (AttributeError, ImportError) as e:
		await ctx.send('```py\n{}: {}\n```'.format(type(e).__name__, str(e)))

@bot.command(name='listguilds', hidden=True)
@checks.is_owner()
async def guild_list(ctx):
	await bot.wait_until_ready()
	for guild in bot.guilds:
		print(guild.name)

if __name__ == '__main__':
	bot.dbhandler = DBHandler()
	bot.log = log
	bot.message_owner = message_owner
	for extension in startup_extensions:
		try:
			bot.load_extension(extension)
		except Exception as e:
			print(f'Failed to load extension {extension}.', file=sys.stderr)
			traceback.print_exc()
	bot.run(credentials.discord['access_token'])
	print('[{}] FJBOT: END'.format(datetime.now()))
