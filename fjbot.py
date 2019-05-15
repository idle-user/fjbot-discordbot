#!/usr/bin/env python3
from datetime import datetime
import sys, traceback
import asyncio

from discord.ext import commands
import discord

from utils.fjclasses import _DbHelper, UserNotRegisteredError, DiscordUser
from utils import config, checks, quickembed


bot = discord.ext.commands.Bot(
	command_prefix=config.general['command_prefix'],
	description=config.general['description'])

def log(content=None, embed=None):
	bot.loop.create_task(discord_log(content=content, embed=embed))

def message_owner(content=None, embed=None):
	bot.loop.create_task(pm_owner(content=content, embed=embed))

async def discord_log(content=None, embed=None):
	await bot.wait_until_ready()
	channel_log = bot.get_channel(config.discord['channel']['log'])
	await channel_log.send(content=content, embed=embed)

async def pm_owner(content=None, embed=None):
	server = bot.get_server(config.discord['guild_id'])
	owner = server.get_member(config.discord['owner_id'])
	if owner:
		await bot.send_message(owner, content=content, embed=message)

@bot.event
async def on_command_error(ctx, error):
	msg = None
	if isinstance(error, commands.CommandNotFound):
		return
	elif isinstance(error, commands.CommandError):
		raise error
	elif isinstance(error, UserNotRegisteredError):
		msg = 'Your Discord is not linked to an existing Matches account.\nUse `!register` or visit http://matches.fancyjesse.com to link to your existing account.'
	elif isinstance(error, commands.CommandInvokeError):
		if isinstance(error.original, asyncio.TimeoutError):
			msg = 'Took too long to confirm. Try again.'
	if msg:
		await ctx.send(embed=quickembed.error(desc=msg, user=DiscordUser(ctx.author)))
	else:
		raise error

@bot.event
async def on_message(ctx):
	if ctx.author.bot or not ctx.content.startswith(config.general['command_prefix']):
		return
	res = _DbHelper().chatroom_command(ctx.content.split(' ')[0])
	if res['success']:
		await ctx.channel.send(res['message'].replace('@mention', ctx.author.mention))
	else:
		tokens = ctx.content.split(' ')
		ctx.content = '{} {}'.format(tokens[0].lower(), ' '.join(tokens[1:]))
	await bot.process_commands(ctx)

@bot.event
async def on_ready():
	bot.start_dt = datetime.now()
	print('[{}] Discord `{}`: START'.format(bot.start_dt, bot.user.name))

@bot.command(name='load', hidden=True)
@commands.is_owner()
async def cog_load(ctx, cog:str):
	try:
		cog = cog if 'cogs.' in cog else 'cogs.{}'.format(cog)
		bot.load_extension(cog)
		await ctx.send('```\n`{}` loaded\n```'.format(cog))
	except (AttributeError, ImportError) as e:
		await ctx.send('```py\n{}: {}\n```'.format(type(e).__name__, str(e)))

@bot.command(name='unload', hidden=True)
@commands.is_owner()
async def cog_unload(ctx, cog:str):
	try:
		cog = cog if 'cogs.' in cog else 'cogs.{}'.format(cog)
		bot.unload_extension(cog)
		await ctx.send('```\n`{}` unloaded\n```'.format(cog))
	except (AttributeError, ImportError) as e:
		await ctx.send('```py\n{}: {}\n```'.format(type(e).__name__, str(e)))

@bot.command(name='reload', hidden=True)
@commands.is_owner()
async def cog_reload(ctx, cog:str):
	try:
		cog = cog if 'cogs.' in cog else 'cogs.{}'.format(cog)
		bot.unload_extension(cog)
		bot.load_extension(cog)
		await ctx.send('```\n`{}` reloaded\n```'.format(cog))
	except (AttributeError, ImportError) as e:
		await ctx.send('```py\n{}: {}\n```'.format(type(e).__name__, str(e)))

@bot.command(name='listguilds', hidden=True)
@commands.is_owner()
async def guild_list(ctx):
	await bot.wait_until_ready()
	for guild in bot.guilds:
		print(guild.name)

if __name__ == '__main__':
	bot.log = log
	bot.message_owner = message_owner
	for extension in config.general['startup_cogs']:
		try:
			bot.load_extension(extension)
		except Exception as e:
			print(f'Failed to load extension {extension}.', file=sys.stderr)
			traceback.print_exc()
	bot.run(config.discord['access_token'])
	print('[{}] Discord `FJBOT`: END'.format(datetime.now()))
