from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Thread
from time import sleep
import asyncio
import sys

import ch

from dbhandler import DBHandler
import credentials


dbhandler = DBHandler()
bot = None
users = set()
messages = []
current_match = {}

class Bot(ch.RoomManager):
	def onInit(self):
		global bot
		bot = self
		self.setNameColor('000099')
		self.setFontColor('000099')
		self.setFontFace('Arial')
		self.setFontSize(14)
		print('[{}] Chatango {}: START'.format(datetime.now(), self.name))

	def onMessage(self, room, user, message):
		global users, messages, last_message

		users.add(user.name)
		msg = '[{}] @{}: {}'.format(room.name, user.name, message.body)
		messages.append(msg)

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
			res = '!resetpw - Get a temporary password for the website | !rate - Rate the current match | !rumble - Get an entry number for the Royal Rumble | !commands - get a list of other commands'
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
			res = ' | '.join(dbhandler.misc_commands())
		elif cmd == '!pmme':
			res = 'Test PM'
		else:
			res = dbhandler.discord_command(cmd)
			if res:
				res = res['response'].replace('\n', ' ')
				if('@mention' in res): res = res.replace('@mention', '@{}'.format(username))
		if res:
			self.sendUserMessage(username, res)

	def verify(self, username):
		data = dbhandler.chatango_username_info(username)
		return data

	def register(self, username):
		if self.verify(username):
			return '@{}, you are already registered. Use !help to get a list of commands'.format(username)
		data = dbhandler.chatango_register(username)
		if data:
			return '@{}, registration was successful! Use !help to get a list of commands.'.format(username)
		else:
			print('chatango.register: Failed to register:',username)
			return False

	def reset_pw(self, username):
		user_id = self.verify(username)['user_id']
		temp = dbhandler.user_temp_password(user_id)
		return 'Visit https://fancyjesse.com/account?temp_pw={}&user_id={}&username={}&project=wwe to set a new password. Link will expire in 30 minutes.'.format(temp, user_id, username)

	def rate_match(self, username, rating=0):
		if not current_match:
			return 'No Current Match set for Rating.'
		try:
			rating = float(rating)
		except:
			rating = 0
		if rating<1 or rating>5:
			return 'Not a valid star rating. (1-5)'
		try:
			if dbhandler.user_rate(self.verify(username)['user_id'], current_match['id'], rating):
				return '{} Star Match rating received.'.format(rating)
		except Exception as e:
			print('Exception:rate_match:',e, username, current_match['id'], rating)

	def royalrumble_entry(self, username, args=[]):
		if not args or args[0] != 'now':
			return 'Login and visit the Event section on https://fancyjesse.com/projects/wwe to join the Rumble! If you have not set a password use !resetpw. Or skip everything and just get an entry nuumber using command "!rumble now"'
		user_id = self.verify(username)['user_id']
		res = dbhandler.royalrumble_check(user_id)
		if res:
			return 'You have already entered as #{} on {}'.format(res['number'], res['dt_entered'])
		res  = dbhandler.royalrumble_entry(user_id)
		if res:
			res = 'You have entered the Royal Rumble as #{}'.format(res)
		else:
			res = 'Unable to join the Royal Rumble. Probably not open yet or you have already entered.'
		return res

async def display_messages(timer=5):
	global messages
	await asyncio.sleep(5)
	while bot._running:
		for msg in messages:
			print(msg)
		print(messages)
		messages = []
		await asyncio.sleep(timer)
		bot.stop()
	print('end while loop display_messages')

async def message_stream(loop):
	executor = ThreadPoolExecutor()
	t_stream = Thread(target=start_bot)
	await loop.run_in_executor(executor, t_stream.start)
	await loop.run_in_executor(executor, t_stream.join)

async def asyncio_test():
	for i in range(1,10):
		print('async message {}'.format(i))
		await asyncio.sleep(1)
		if i==5:
			bot.stop()

def start_bot():
	Bot.easy_start(credentials.chatango['rooms'], credentials.chatango['username'], credentials.chatango['secret'])
	
if __name__ == '__main__':
	try:
		print('chatango.py START')
		loop = asyncio.get_event_loop()
		tasks = [
			asyncio.ensure_future(display_messages()),
			asyncio.ensure_future(message_stream(loop)),
			asyncio.ensure_future(asyncio_test())
		]
		print('Tasks Created.')
		print('Starting Asyncio loop.')	
		loop.run_until_complete(asyncio.gather(*tasks))
		print('End Asyncio')
	except KeyboardInterrupt:
		pass
	finally:
		bot.stop()
		print('chatango.py END')
