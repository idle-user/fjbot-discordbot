from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Thread
from time import sleep
import asyncio
import sys

import discord
from discord.ext import commands

from lib import ch
from utils import checks, credentials


chbot = None
class Chatango:

	def __init__(self, bot):
		self.bot = bot
		self.channel_chatango = discord.Object(id=credentials.discord['channel']['chatango'])
		self.bot.loop.create_task(self.chatango_bot_task())
		self.bot.loop.create_task(self.chatango_log_task())

	def __unload(self):
		global chbot
		chbot.stop()

	class ChBot(ch.RoomManager):
		def onInit(self):
			global chbot
			chbot = self
			self.buffer = []
			self.users = []
			self.setNameColor('000099')
			self.setFontColor('000099')
			self.setFontFace('Arial')
			self.setFontSize(14)
			print('[{}] Chatango {}: START'.format(datetime.now(), self.name))
		def onMessage(self, room, user, message):
			self.users.append(user.name)
			msg = '[{}] @{}: {}'.format(room.name, user.name, message.body)
			self.buffer.append(msg)
			if user.name==self.name.lower():
				return
			args = message.body.lower().split(' ')
			if  not args[0].startswith('!') or user.name.startswith('#'):
				return
			if not self.verify(user.name) and not 'register' in args[0]:
				msg = 'You must first register to use commands. Please use command `!register`.'
				self.sendUserMessage(user.name, msg)
				# room.message('@{}, {}'.format(user.name, msg))
			else:
				try:
					self.command_handler(user.name, args[0], args[1:])
				except Exception as e:
					print('Exception:onMessage:', e, msg)
		def onPMMessage(self, pm, user, body):
			print('onPMMessage:', user, body)
			args = body.split(' ')
			if  not args[0].startswith('!') or user.name.startswith('#'):
				return
			if not self.verify(user.name) and not 'register' in args[0]:
				self.sendUserMessage(user.name, 'You must first register to use commands. Please use command `!register`.')
			else:
				try:
					self.command_handler(user.name, args[0], args[1:])
				except Exception as e:
					print('Exception: onPMMessge:',e)
		def onFloodWarning(self, room):
			print('onFloodWarning', room)
		def onFloodBan(self, room):
			print('onFloodBan:',room)
		def sendRoomMessage(self, room, msg):
			room = self.getRoom(room)
			if room:
				room.message(msg)
				return True
			return False
		def sendUserMessage(self, username, msg):
			print('sendUserMessage:',username, msg)
			try:
				if sys.getsizeof(msg) > 800:
					tokens = msg.split()
					mid = round(len(tokens)/2)
					self.pm.message(ch.User(username), '{} ...'.format(' '.join(tokens[:mid])))
					sleep(0.5)
					self.pm.message(ch.User(username), '... {}'.format(' '.join(tokens[mid:])))
				else:
					self.pm.message(ch.User(username), msg)
			except:
				print('Failed to PM User:', username)
		def command_handler(self, username, cmd, args=[]):
			res = False
			if cmd == '!register':
				res = self.register(username)
			elif cmd == '!help':
				res = '!resetpw - Get a temporary password for the website | !rate - Rate the current match | !rumble - Get an entry number the Royal Rumble | !commands - get a list of other commands'
			elif cmd == '!resetpw':
				res = self.reset_pw(username)
			elif cmd == '!rate':
				try:
					res = self.rate_match(username, args[0])
				except Exception as e:
					print('Exception:command_handler:',e, username, cmd, args)
			elif cmd == '!rumble':
				res = self.royalrumble_entry(username, args)
			elif cmd == '!commands':
				res = ' | '.join(self.myapi.dbhandler.misc_commands())
			elif cmd == '!pmme':
				res = 'Test PM'
			else:
				res = self.myapi.dbhandler.discord_command(cmd)
				if res:
					res = res['response'].replace('\n', ' ')
					if('@mention' in res): res = res.replace('@mention', '@{}'.format(username))
			if res:
				self.sendUserMessage(username, res)
		def verify(self, username):
			data = self.myapi.dbhandler.chatango_username_info(username)
			return data
		def register(self, username):
			if self.verify(username):
				return '@{}, you are already registered. Use `!help` to get a list of commands'.format(username)
			data = self.myapi.dbhandler.chatango_register(username)
			if data:
				return '@{}, registration was successful! Remember to set a password for your account by using `!resetpw`. For other commands, use `!help`.'.format(username)
			else:
				print('chatango.register: Failed to register:',username)
				return False
		def reset_pw(self, username):
			user_id = self.verify(username)['user_id']
			temp = self.myapi.dbhandler.user_temp_password(user_id)
			return 'Visit https://fancyjesse.com/account?temp_pw={}&user_id={}&username={}&project=wwe to set a new password. Link will expire in 30 minutes.'.format(temp, user_id, username)
		def rate_match(self, username, rating=0):
			if not self.myapi.current_match:
				return 'No Current Match set for Rating.'
			try:
				rating = float(rating)
			except:
				rating = 0
			if rating<1 or rating>5:
				return 'Not a valid star rating. (1-5)'
			try:
				if self.myapi.dbhandler.user_rate(self.verify(username)['user_id'], self.myapi.current_match['id'], rating):
					return '{} Star Match rating received.'.format(rating)
			except Exception as e:
				print('Exception:rate_match:',e, username, self.myapi.current_match['id'], rating)
		def royalrumble_entry(self, username, args=[]):
			if not args or args[0] != 'now':
				return 'Login and visit the Event section on https://fancyjesse.com/projects/wwe to join the Rumble! If you have not set a password, use !resetpw. Or skip everything and just get an entry nuumber using command "!rumble now"'
			user_id = self.verify(username)['user_id']
			res = self.myapi.dbhandler.royalrumble_check(user_id)
			if res:
				return 'You have already entered as #{} on {}'.format(res['number'], res['dt_entered'])
			res  = self.myapi.dbhandler.royalrumble_entry(user_id)
			if res:
				res = 'You have entered the Royal Rumble as #{}'.format(res)
			else:
				res = 'Unable to join the Royal Rumble. Probably not open yet or you have already entered.'
			return res

	def start_chbot(self):
		self.ChBot.easy_start(credentials.chatango['rooms'], credentials.chatango['username'], credentials.chatango['secret'])		

	async def chatango_bot_task(self):
		await self.bot.wait_until_ready()
		executor = ThreadPoolExecutor()
		t_stream = Thread(target=self.start_chbot)
		await self.bot.loop.run_in_executor(executor, t_stream.start)
		await self.bot.loop.run_in_executor(executor, t_stream.join)
		print('END chatango_bot_task')
	
	async def wait_until_chbot_running(self, limit=30):
		while limit > 0:
			try:
				return chbot._running == True
			except:
				pass
			await asyncio.sleep(1)
			limit = limit - 1

	async def chatango_log_task(self):
		global chbot
		await self.bot.wait_until_ready()
		await self.wait_until_chbot_running()
		chbot.myapi = self.bot
		while not self.bot.is_closed and chbot._running:
			while chbot.buffer:
				await self.bot.send_message(self.channel_chatango, '```{}```'.format(chbot.buffer.pop(0)))
				await asyncio.sleep(0.2)
			await asyncio.sleep(1)
		print('END chatango_log_task')

	@commands.command(name='ch', pass_context=True)
	@checks.is_owner()
	async def send_message(self, ctx, message):
		if message == '!ad':
			message = discord_ad
		await self.bot.say('Send message to Chatango? [Y/N]```{}```'.format(message))
		confirm = await self.bot.wait_for_message(timeout=10.0, author=ctx.message.author, check=checks.confirm)
		if confirm and confirm.content.upper()=='Y':
			ch_rooms = []
			for ch_room in credentials.chatango['rooms']:
				if chbot.sendRoomMessage(ch_room, message):
					ch_rooms.append(ch_room)
			await self.bot.say('{}, Discord message sent to Chatango [{}].'.format(ctx.message.author.mention, ','.join(ch_rooms)))
		else:
			await self.bot.say('{}, Chatango message cancelled.'.format(ctx.message.author.mention))			

	@commands.command(name='chusers', pass_context=True)
	@checks.is_owner()
	async def display_users(ctx):
		await self.bot.say('Chatango User List ({})\n {}'.format(len(chbot.users), chbot.users))

def setup(bot):
	bot.add_cog(Chatango(bot))
