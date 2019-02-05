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
channel_log = discord.Object(id=credentials.discord['channel']['log'])


def log(message):
	print(message)
	bot.loop.create_task(discord_log(message))

def message_owner(message):
	print(message)
	bot.loop.create_task(pm_owner(message))

async def discord_log(message):
	await bot.wait_until_ready()
	await bot.send_message(channel_log, '```{}```'.format(message))

async def pm_owner(message):
	server = bot.get_server(credentials.discord['server_id'])
	owner = server.get_member(credentials.discord['owner_id'])
	if owner:
		await bot.send_message(owner, message)

@bot.event
async def on_command_error(error, ctx):
	if 'is not found' in str(error) or ctx.message.channel.is_private:
		return
	else:
		bot.log('{}\n[{}] {}: {}'.format(error, ctx.message.channel, ctx.message.author, ctx.message.content))
		#raise error

@bot.event
async def on_member_join(member):
	channel_general = discord.Object(id=credentials.discord['channel']['general'])
	role = discord.utils.get(member.server.roles, id=credentials.discord['role']['default'])
	await bot.add_roles(member, role)
	await bot.send_message(channel_general, 'Welcome to {}, {}! Say hi!'.format(member.server.name, member.mention))

@bot.event
async def on_message(message):
	if message.author.bot or not message.content.startswith('!'):
		return
	res = bot.dbhandler.discord_command(message.content.split(' ')[0])
	if res:
		await bot.send_message(message.channel, res['response'].replace('@mention', message.author.mention))
		bot.dbhandler.discord_command_cnt(res['id'])
	else:
		tokens = message.content.split(' ')
		message.content = '{} {}'.format(tokens[0].lower(), ' '.join(tokens[1:]))
		await bot.process_commands(message)

@bot.event
async def on_ready():
	bot.start_dt = datetime.now()
	bot.log('[{}] Discord {}: START'.format(bot.start_dt, bot.user.name))

@bot.command(name='load', hidden=True)
@checks.is_owner()
async def cog_load(cog:str):
	try:
		cog = cog if 'cogs.' in cog else 'cogs.{}'.format(cog)
		bot.load_extension(cog)
		await bot.say('```{} loaded```'.format(cog))
	except (AttributeError, ImportError) as e:
		await bot.say('```py\n{}: {}\n```'.format(type(e).__name__, str(e)))

@bot.command(name='unload', hidden=True)
@checks.is_owner()
async def cog_unload(cog:str):
	try:
		cog = cog if 'cogs.' in cog else 'cogs.{}'.format(cog)
		bot.unload_extension(cog)
		await bot.say('```{} unloaded```'.format(cog))
	except (AttributeError, ImportError) as e:
		await bot.say('```py\n{}: {}\n```'.format(type(e).__name__, str(e)))

@bot.command(name='reload', hidden=True)
@checks.is_owner()
async def cog_reload(cog:str):
	try:
		cog = cog if 'cogs.' in cog else 'cogs.{}'.format(cog)
		bot.unload_extension(cog)
		bot.load_extension(cog)
		await bot.say('```{} reloaded```'.format(cog))
	except (AttributeError, ImportError) as e:
		await bot.say('```py\n{}: {}\n```'.format(type(e).__name__, str(e)))

if __name__ == '__main__':
	try:
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
	except KeyboardInterrupt:
		pass
	finally:
		bot.logout()
		print('[{}] FJBOT: END'.format(datetime.now()))
		print('Total Tasks: {}'.format(len(asyncio.Task.all_tasks())))
		print('Active Tasks: {}'.format(len([t for t in asyncio.Task.all_tasks() if not t.done()])))
