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
			self.setFontFace('Times')
			self.setFontSize(14)
		def onMessage(self, room, user, message):
			self.users.append(user.name)
			msg = '[{}] @{}: {}'.format(room.name, user.name, message.body)
			self.buffer.append(msg)
			if user.name==self.name.lower():
				return
			args = message.body.lower().split(' ')
			if not args[0].startswith('!') or user.name.startswith('#'):
				return
			elif '!discord' in args[0]:
				msg = 'Discord Channel: {}'.format(credentials.discord['invite_link'])
				self.sendUserMessage(user.name, msg)
				self.bot.log('[chatango] sendUserMessage:{} - {}'.format(user.name, msg))
			elif not self.verify(user.name) and not 'register' in args[0]:
				msg = 'You must first register to use commands. Please use command `!register`.'
				self.sendUserMessage(user.name, msg)
				# room.message('@{}, {}'.format(user.name, msg))
			else:
				try:
					self.command_handler(user.name, args[0], args[1:])
				except Exception as e:
					self.bot.log('[chatango] Exception:onMessage: {} {}'.format(e, msg))
		def onPMMessage(self, pm, user, body):
			self.bot.log('[chatango] onPMMessage:{} - {}'.format(user, body))
			args = body.split(' ')
			if  not args[0].startswith('!') or user.name.startswith('#'):
				return
			if not self.verify(user.name) and not 'register' in args[0]:
				self.sendUserMessage(user.name, 'You must first register to use commands. Please use command `!register`.')
			else:
				try:
					self.command_handler(user.name, args[0], args[1:])
				except Exception as e:
					self.bot.log('[chatango] Exception: onPMMessge:{}'.format(e))
		def onFloodWarning(self, room):
			self.bot.log('[chatango] onFloodWarning:{}'.format(room))
		def onFloodBan(self, room):
			self.bot.log('[chatango] onFloodBan:{}'.format(room))
		def sendRoomMessage(self, room, msg):
			room = self.getRoom(room)
			if room:
				room.message(msg)
				return True
			return False
		def sendUserMessage(self, username, msg):
			#msg = '{} (Discord Channel: {})'.format(msg, credentials.discord['invite_link'])
			#self.bot.log('[chatango] sendUserMessage:{} - {}'.format(username, msg))
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
				self.bot.log('[chatango] Failed to PM User:{}'.format(username))
		def command_handler(self, username, cmd, args=[]):
			cmd = cmd.lower()
			res = False
			if cmd == '!register':
				res = self.register(username)
			elif cmd == '!login':
				res = self.login_link(username)
			elif cmd == '!help':
				res = '!resetpw - Get a temporary password for the website | !rate - Rate the current match | !mypoints - View your Match Points | !bet - Bet on a current match with your Match Points | !rumble - Get an entry number the Royal Rumble | !commands - get a list of other commands'
			elif cmd == '!resetpw':
				res = self.reset_pw(username)
			elif cmd in ['!mypoints', '!points', '!mystats', '!stats']:
				res = self.display_stats(username)
			elif cmd == '!matches':
				res = self.open_matches()
			elif cmd == '!bet':
				try:
					res = self.bet_match(username, args)
				except Exception as e:
					self.bot.log('[chatango] Exception:command_handler: {} {} {} {}'.format(username, cmd, e ,args))
			elif cmd == '!rate':
				try:
					res = self.rate_match(username, args[0])
				except Exception as e:
					self.bot.log('[chatango] Exception:command_handler: {} {} {} {}'.format(username, cmd, e ,args))
			elif cmd == '!rumble':
				res = self.royalrumble_entry(username, args)
			elif cmd == '!commands':
				res = ' | '.join(self.bot.dbhandler.misc_commands())
			elif cmd == '!test':
				res = 'This is a test message\nTest'
			else:
				res = self.bot.dbhandler.discord_command(cmd)
				if res:
					res = res['response']
					if('@mention' in res): res = res.replace('@mention', '@{}'.format(username))
			if res:
				self.sendUserMessage(username, res)
		def verify(self, username):
			try:
				user = self.bot.dbhandler.user_by_chatango(username)
				return user
			except:
				return False
		def register(self, username):
			if self.verify(username):
				return '@{}, you are already registered. Use `!help` to get a list of commands'.format(username)
			data = self.bot.dbhandler.chatango_register(username)
			if data:
				self.bot.log('[chatango] {} has registered.'.format(username))
				return '@{}, registration was successful! You can now use !login to get a quick login link for the website. Remember to set a password for your account by using `!resetpw`. For other commands, use `!help`.'.format(username)
			else:
				self.bot.log('[chatango] Failed to register: {}'.format(username))
				return False
		def login_link(self, username):
			user = self.verify(username)
			token = self.bot.dbhandler.user_login_token(user.id)
			self.bot.log('[chatango] {} requested a login link.'.format(username))
			return 'https://fancyjesse.com/projects/matches?uid={}&token={} (Link expires in 5 minutes)'.format(user.id, token)

		def reset_pw(self, username):
			user = self.verify(username)
			temp = self.bot.dbhandler.user_temp_password(user.id)
			return 'Visit https://fancyjesse.com/account?temp_pw={}&user_id={}&username={}&project=matches to set a new password. Link will expire in 30 minutes.'.format(temp, user.id, user.username)
		def open_matches(self):
			matches = self.bot.dbhandler.open_matches()
			if matches:
				return ' | '.join(['[{} - {}]'.format(m.match_type, m.contestants) for m in matches])
			else:
				return 'No Open Matches available.'
		def display_stats(self, username):
			try:
				stats = self.bot.dbhandler.user_stats(self.verify(username).id)
				return 'Total Points: {:,} | Available Points: {:,} | Wins: {} | Losses: {} | Profile: https://fancyjesse.com/projects/matches/user?user_id={}'.format(stats['s2_total_points'], stats['s2_available_points'], stats['s2_wins'], stats['s2_losses'], stats['id'])
			except Exception as e:
				self.bot.log('[chatango] Exception:display_stats: {} {}'.format(username, e))
		def bet_match(self, username, args):
			try:
				bet = int(args[0])
				contestant = str(args[1])
			except:
				return 'Invalid `!bet` format. Use `!bet [bet_amount] [contestant]`'
			if bet<1:
				return 'Invalid bet amount. Try again'
			try:
				user = self.bot.dbhandler.user_stats(self.verify(username).id)
				if user['s2_available_points'] < bet:
					return 'Insufficient points available. You only have `{}` points. Please try again.'.format(user['s2_available_points'])
				matches = self.bot.dbhandler.open_matches()
				if not matches:
					return 'No Open Matches found. Enter `!matches` to see a list of Open Matches.'
				match = None
				for m in matches:
					if m.contains_contestant(contestant):
						match = m
						team_id = m.team_by_contestant(contestant)
						break
				if not match:
					return 'Match not found with `{}`. Enter `!matches` to see a list of Open Matches. Please try again.'.format(contestant)
				if not match.bet_open:
					return 'Match bets are closed. Enter `!matches` to see a list of Open Matches. Please try again.'
				team_members = match.contestants_by_team(team_id)
				ub = self.bot.dbhandler.user_bet_check(user['id'], match.id)
				if ub:
					return 'You already have a {:,} point bet placed on {}.'.format(ub['points'], team_members)
				if self.bot.dbhandler.user_bet(user['id'], match.id, team_id, bet):
					pot = self.bot.dbhandler.match(match.id).base_pot
					self.bot.log('[chatango] {} placed a {:,} point bet on Match {} for {}.'.format(username, bet, match.id, team_members))
					return 'You placed a `{:,}` point bet on Match {} for **{}**! Match Base Pot is now **{:,}** points.'.format(bet, match.id, team_members, pot)
				else:
					self.bot.log('[chatango] Unable to process bet. user:{} bet:{} Match:{} members:{}.'.format(username, bet, match.id, team_members))
					return 'Unable to process your bet. Issue has been reported. Please try again later.'
			except Exception as e:
				self.bot.log('[chatango] Exception:bet_match: {} {} {} {}'.format(e, username, bet, contestant))
		def rate_match(self, username, rating=0):
			if not self.bot.current_match:
				return 'No Current Match set for Rating.'
			match_id = self.bot.current_match.id
			try:
				rating = float(rating)
			except:
				rating = 0
			if rating<1 or rating>5:
				return 'Not a valid star rating. (1-5)'
			try:
				if self.bot.dbhandler.user_rate(self.verify(username).id, match_id, rating):
					self.bot.log('[chatango] {} rated Match {} {} stars.'.format(username, match_id, rating))
					return '{} Star Match rating received.'.format(rating)
			except Exception as e:
				self.bot.log('[chatango] Exception:rate_match: {} {} {} {}', e, username, match_id, rating)
		def royalrumble_entry(self, username, args=[]):
			self.bot.log('[chatango] {} requested a Rumble login link.'.format(username))
			user = self.verify(username)
			if not args or args[0] != 'now':
				token = self.bot.dbhandler.user_login_token(user.id)
				return 'Visit the following link to join the Rumble! https://fancyjesse.com/projects/matches/royalrumble?uid={}&token={} (Link expires in 5 minutes)'.format(user.id, token)
			res = self.bot.dbhandler.royalrumble_check(user.id)
			if res:
				return 'You have already entered as #{} on {}'.format(res['number'], res['dt_entered'])
			res  = self.bot.dbhandler.royalrumble_entry(user.id)
			if res:
				self.bot.log('[chatango] {} Entered the Rumble as #{}.'.format(username, res))
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
		self.bot.log('END chatango_bot_task')

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
		chbot.bot = self.bot
		self.bot.log('[{}] Chatango {}: START'.format(datetime.now(), chbot.name))
		self.bot.log('Starting Chatango Stream ...')
		while not self.bot.is_closed and chbot._running:
			while chbot.buffer:
				await self.bot.send_message(self.channel_chatango, '```{}```'.format(chbot.buffer.pop(0)))
				await asyncio.sleep(0.5)
			await asyncio.sleep(1)
		self.bot.log('END chatango_log_task')

	@commands.command(name='ch', pass_context=True)
	@checks.is_owner()
	async def send_message(self, ctx, *, message:str):
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
		await self.bot.say('```Chatango User List ({})\n {}```'.format(len(chbot.users), chbot.users))

def setup(bot):
	bot.add_cog(Chatango(bot))
