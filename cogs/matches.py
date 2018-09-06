import asyncio
import datetime

from discord.ext import commands
import discord

from cogs import chatango
from utils.dbhandler import DBHandler
from utils import checks, credentials


class Matches:

	def __init__(self, bot):
		self.bot = bot
		self.dbhandler = DBHandler()
		self.bot.current_match = None
		self.channel_general = discord.Object(id=credentials.discord['channel']['general'])
		self.channel_ppv = discord.Object(id=credentials.discord['channel']['ppv'])
		self.channel_raw = discord.Object(id=credentials.discord['channel']['raw'])
		self.channel_sd = discord.Object(id=credentials.discord['channel']['sdlive'])
		self.bot.loop.create_task(self.showtime_schedule_task())

	async def showtime_schedule_task(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed:
			event = self.dbhandler.next_event()
			dt = datetime.datetime.now()
			timer = (event['dt'] - dt).total_seconds()
			self.bot.log('showtime_schedule_task: sleep_until:{}, event:{}'.format(dt+datetime.timedelta(seconds=timer), event['name']))
			await asyncio.sleep(timer)
			if 'RAW' in event['name']:
				await self.bot.send_message(self.channel_raw, "@everyone, it's time for **Monday Night RAW**!")
			elif 'SmackDown' in event['name']:
				await self.bot.send_message(self.channel_sd, "@everyone, it's time for **SmackDown LIVE**!")
			elif event['ppv']:
				await self.bot.send_message(self.channel_ppv, '@everyone, **{}** has begun!'.format(event['name']))
			else:
				self.bot.log('{} {}'.format(event['name'], event['dt']))
		self.bot.log('END showtime_schedule_task')
		
	@commands.command(name='ratestart', pass_context=True)
	async def start_match_rating(self, ctx, match_id:str=None):
		owner = ctx.message.server.get_member(credentials.discord['owner_id'])
		user = self.dbhandler.user_by_discord(ctx.message.author.id)
		if user['access']<2:
			await self.bot.send_message(owner, '```{}\n[#{}] {}: {}```'.format('Invalid Command', ctx.message.channel, ctx.message.author, ctx.message.content))	
			return
		
		try:
			if not match_id:
				match_id = self.dbhandler.latest_match()['id']		
			match_id = int(match_id)
		except:
			await self.bot.say('Invalid `!startrating` format.\n`!startrating [match_id]`')
			return
		
		m = self.dbhandler.match(match_id)
		
		if m:
			await self.bot.say('`Start Rating on [{} | {}]? [Y/N]`'.format(m.match_type, m.contestants))
			confirm = await self.bot.wait_for_message(timeout=10.0, author=ctx.message.author, check=checks.confirm)
			if not confirm:
				await self.bot.say('You took too long to confirm. Try again, {}.'.format(ctx.message.author.mention))
			else:
				confirm.content = confirm.content.upper()
				if confirm.content=='Y':
					self.bot.current_match = m
					msg = 'Match Rating has begun! Use command `!rate [number]` to give the match a 1-5 star rating. [{0.match_type} | {0.contestants}]'.format(m)
					await self.bot.say(msg)
					for ch_room in credentials.chatango['rooms']:
						chatango.chbot.sendRoomMessage(ch_room, msg)
				else:
					await self.bot.say('`RateStart cancelled.`')
		else:
			await self.bot.say('`Match not found.`')

	@commands.command(name='rateend', pass_context=True)
	async def end_match_rating(self, ctx):
		user = self.dbhandler.user_by_discord(ctx.message.author.id)
		if user['access']<2:
			await self.bot.send_message(owner, '```{}\n[#{}] {}: {}```'.format('Invalid Command', ctx.message.channel, ctx.message.author, ctx.message.content))	
			return
		if self.bot.current_match:
			match_id = self.bot.current_match.id
			self.bot.current_match = {}
			m = self.dbhandler.match(match_id)
			msg = '`Match Rating has ended. Received a total of {0.star_rating} ({0.user_rating_avg:.3f}). [{0.match_type} | {0.contestants}]`'.format(m)
			await self.bot.say(msg)
			for ch_room in credentials.chatango['rooms']:
				chatango.chbot.sendRoomMessage(ch_room, msg)
		else:
			await self.bot.say('`No current match set.`')
		
	@commands.command(name='id', pass_context=True)
	async def send_userid(self, ctx):
		await self.bot.send_message(ctx.message.author, 'Your discord_id is: `{}`\nLink it to your http://matches.fancyjesse.com profile.'.format(ctx.message.author.id))
		await self.bot.say('{}, your ID has been DMed. Please visit http://matches.fancyjesse.com to link your account.'.format(ctx.message.author.mention))

	@commands.command(name='verify', pass_context=True)
	async def verify_user_account(self, ctx):
		user = self.dbhandler.user_by_discord(ctx.message.author.id)
		if user:
			await self.bot.say('Your Discord is successfully linked to `{}` on http://matches.fancyjesse.com'.format(user['username']))
		else:
			await self.bot.say('You are not registered.\nPlease visit http://matches.fancyjesse.com to register.\nThen link your Discord account by using command `!id`.')

	@commands.command(name='mypage', pass_context=True)
	async def user_page(self, ctx):
		user = self.dbhandler.user_by_discord(ctx.message.author.id)
		if user:
			await self.bot.say("{}'s Matches Page\nhttps://fancyjesse.com/projects/matches/user?user_id={}".format(ctx.message.author.mention, user['id']))
		else:
			await self.bot.say('You are not registered.\nPlease visit http://matches.fancyjesse.com to register.\nThen link your Discord account by using command `!id`.')

	@commands.command(name='addevents', aliases=['addweeklyevents'], pass_context=True, hidden=True)
	@checks.is_mod()
	async def insert_weekly_events(self, ctx):
		d = datetime.date.today()
		m = d.month
		add_cnt = 0
		while d.month == m:
			if d.weekday() == 0:
				name = 'RAW'
				if self.dbhandler.add_event(d, name):
					add_cnt = add_cnt + 1
					msg = '{} {} added.'.format(name, d)
					self.bot.log('`{}`'.format(msg))
					await self.bot.say(msg)
			elif d.weekday() == 1:
				name = 'SmackDown LIVE'
				if self.dbhandler.add_event(d, name):
					add_cnt = add_cnt + 1
					msg = '`{} {}` added.'.format(name, d)
					self.bot.log('`{}`'.format(msg))
					await self.bot.say(msg)
			d = d + datetime.timedelta(1)
		if add_cnt == 0:
			await self.bot.say('No events to be added this month.')

	@commands.command(name='events', aliases=['ppv','ppvs'])
	async def upcomming_events(self):
		ppvs = self.dbhandler.events()
		await self.bot.say('```Upcoming PPVs\n-------------\n{}```'.format('\n'.join(['{} - {}'.format(e['date'],e['name']) for e in ppvs])))

	@commands.command(name='bio', pass_context=True)
	async def superstar_bio(self, ctx, *, content:str):
		try:
			superstar = content
		except:
			await self.bot.say('Invalid `!bio` format.\n`!bio [superstar]`')
			return

		superstars = self.dbhandler.superstar_search('%'+superstar.replace(' ','%')+'%')
		if not superstars:
			await self.bot.say("Unable to find Superstars matching '{}'".format(superstar))
			return
		else:
			if len(superstars)>1: 
				msg = 'Select Superstar from List ...\n```'
				for i,e in enumerate(superstars):
					msg = msg + '{}. {}\n'.format(i+1, e['name'])
				msg = msg + '```'
				await self.bot.say(msg)
				response = await self.bot.wait_for_message(timeout=15.0, author=ctx.message.author, check=checks.is_number)
				if not response:
					await self.bot.say('You took too long to confirm. Try again, {}.'.format(ctx.message.author.mention))
				else:
					try:
						index = int(response.content)
						bio = superstars[index-1]
					except:
						await self.bot.say('Invalid Index.')
						return
			else:
				bio = superstars[0]

			name = bio['name'] + (' ({})'.format(bio['twitter_name']) if bio['twitter_name'] else '')
			height = 'Height: {}\n'.format(bio['height']) if bio['height'] else ''
			weight = 'Weight: {}\n'.format(bio['weight']) if bio['weight'] else ''
			hometown = 'Hometown: {}\n'.format(bio['hometown']) if bio['hometown'] else ''
			signature_move = 'Signature Move(s): {}\n'.format(bio['signature_move']) if bio['signature_move'] else ''
			dob = ''
			if bio['dob']:
				today = datetime.datetime.now().date()
				age = today.year - bio['dob'].year - ((today.month, today.day) < (bio['dob'].month, bio['dob'].day))
				dob = 'DOB: {} ({})\n'.format(bio['dob'], age)		
			msg = '{}\n```{}\n-------------\n{}{}{}{}{}\n\n{}```'.format(bio['official_image_url'], name, height, weight, dob, hometown, signature_move, bio['official_bio'])
			if len(msg)>2000:
				bio['official_bio'] = bio['official_bio'][0:len(bio['official_bio'])-(len(msg)-1995)]+' ...'
				msg = '{}\n```{}\n-------------\n{}{}{}{}{}\n\n{}```'.format(bio['official_image_url'], name, height, weight, dob, hometown, signature_move, bio['official_bio'])
			await self.bot.say(msg)

	@commands.command(name='birthdays')
	async def superstar_birthdays(self):
		bdays = self.dbhandler.superstar_birthdays()
		await self.bot.say('```Birthdays This Month\n-------------\n{}```'.format('\n'.join(['[{}] {}'.format(b['dob'],b['name']) for b in bdays])))

	@commands.command(name='superstars', aliases=['superstarlist', 'listsuperstars'])
	async def all_superstars(self):
		sl = self.dbhandler.superstars()
		sl = [s['name'] for s in sl]
		await self.bot.say('```{}```'.format('\n'.join(sl)))

	@commands.command(name='leaderboard', aliases=['leaderboards'])
	async def current_leaderboard(self):
		lb = self.dbhandler.leaderboard()
		lb = ['{}. {} ({:,})'.format(i+1,l['username'],l['s2_total_points']) for i, l in enumerate(lb)]
		await self.bot.say('```TOP 10 (Season 2)\n------\n{}```'.format('\n'.join(lb)))

	@commands.command(name='leaderboard_s1', aliases=['leaderboards1', 's1leaderboard'])
	async def leaderboard_season1(self):
		lb = self.dbhandler.leaderboard_s1()
		lb = ['{}. {} ({:,})'.format(i+1,l['username'],l['s1_total_points']) for i, l in enumerate(lb)]
		await self.bot.say('```TOP 10 (Season 1)\n------\n{}```'.format('\n'.join(lb)))

	@commands.command(name='titles', aliases=['champions','champs'])
	async def current_champions(self):
		ts = self.dbhandler.titles()
		ts = ['{}\n{}'.format(t['title'], t['superstar']) for t in ts]
		await self.bot.say('```Current Champions\n----------\n{}```'.format('\n\n'.join(ts)))

	@commands.command()
	async def rumble(self):
		await self.bot.say('Join the Rumble at: https://fancyjesse.com/projects/matches/royalrumble')

	@commands.command(name='stats', aliases=['mystats'], pass_context=True)
	async def user_stats(self, ctx):
		user = self.dbhandler.user_by_discord(ctx.message.author.id)
		if user:
			user = self.dbhandler.user_stats(user['id'])
			try:
				ratio = '{:.3f}'.format(user['s2_wins']/user['s2_losses'])
			except:
				ratio = 'N/A'
			await self.bot.say('```Username: {}\nWins: {}\nLosses: {}\nRatio: {}```'.format(user['username'], user['s2_wins'], user['s2_losses'], ratio))
		else:
			await self.bot.say('You are not registered.\nPlease visit http://matches.fancyjesse.com to register.\nThen link your Discord account by using command `!id`.')

	@commands.command(name='stats_s1', aliases=['s1stats', 's1_stats'], pass_context=True)
	async def user_stats_season1(self, ctx):
		user = self.dbhandler.user_by_discord(ctx.message.author.id)
		if user:
			user = self.dbhandler.user_stats(user['id'])
			try:
				ratio = '{:.3f}'.format(user['s1_wins']/user['s1_losses'])
			except:
				ratio = 'N/A'
			await self.bot.say('```Username: {}\nPoints: {:,}\nWins: {}\nLosses: {}\nRatio: {}```'.format(user['username'], user['s1_points'], user['s1_wins'], user['s1_losses'], ratio))
		else:
			await self.bot.say('You are not registered.\nPlease visit http://matches.fancyjesse.com to register.\nThen link your Discord account by using command `!id`.')

	@commands.command(name='points', aliases=['mypoints', ], pass_context=True)
	async def user_points(self, ctx):
		user = self.dbhandler.user_by_discord(ctx.message.author.id)
		if user:
			user = self.dbhandler.user_stats(user['id'])
			await self.bot.say('```Username: {}\nTotal Points: {:,}\nAvailable Points: {:,}```'.format(user['username'], user['s2_total_points'], user['s2_available_points']))
		else:
			await self.bot.say('You are not registered.\nPlease visit http://matches.fancyjesse.com to register.\nThen link your Discord account by using command `!id`.')

	@commands.command(name='bets', aliases=['mybets'], pass_context=True)
	async def user_current_bets(self, ctx):
		user = self.dbhandler.user_by_discord(ctx.message.author.id)
		if user:
			bets = self.dbhandler.user_bets(user['id'])
			if bets:
				await self.bot.say("{}'s Current Bets\n```{}```".format(ctx.message.author.mention, '\n'.join(['Match {}\n  {:,} points on {}\n  Potential Pot Winnings: {:,} ({}%)'.format(bet['match_id'], bet['points'], bet['contestants'], bet['potential_cut_points'], bet['potential_cut_pct']*100) for bet in bets])))
			else:
				await self.bot.say('{} has no bets placed on Matches.'.format(ctx.message.author.mention))
		else:
			await self.bot.say('You are not registered.\nPlease visit http://matches.fancyjesse.com to register.\nThen link your Discord account by using command `!id`.')

	@commands.command(name='match')
	async def match(self, *args):
		try:
			match_id = int(args[0])
		except:
			await self.bot.say('Invalid `!match` format.\n`!match [match_id]`')
			return
		m = self.dbhandler.match(match_id)
		if m:
			await self.bot.say('```{}```'.format(m.display_full()))
		else:
			await self.bot.say('Match `{}` not found.'.format(match_id))

	@commands.command(name='matches', aliases=['openmatches'])
	async def open_matches(self):
		match_list = self.dbhandler.open_matches()
		if match_list:
			msg = 'Open Matches\n------------'
			for m in match_list:
				m_display = m.display_full()
				if len(msg + m_display) > 2000:
					await self.bot.say('```{}```'.format(msg))
					msg = '...\n\n'
				else:
					msg = msg + '\n\n'
				msg = msg + m_display
			await self.bot.say('```{}```'.format(msg))
		else:
			await self.bot.say('No open bet matches available.')

	@commands.command(name='bet', pass_context=True)
	async def place_match_bet(self, ctx, *args):
		user = self.dbhandler.user_by_discord(ctx.message.author.id)
		if user:
			try:
				if len(args) == 2:
					bet = int(args[0])
					superstar = args[1]
					match_id = 0
				else:
					bet = int(args[0])
					match_id = int(args[1])
					team_id = int(args[2])
			except:		
				await self.bot.say('Invalid `!bet` format.\n`!bet [bet_amount] [contestant]`\n`!bet [bet_amount] [match_id] [team]`')
				return
			if bet<1:
				await self.bot.say('Invalid bet. Try again, {}.'.format(ctx.message.author.mention))
				return
			user = self.dbhandler.user_stats(user['id'])
			if user['s2_available_points'] < bet:
				await self.bot.say('Insufficient points available ({0}). Try again, {1}.'.format(user['s2_available_points'], ctx.message.author.mention))
				return
			matches = self.dbhandler.open_matches()
			if not matches:
				await self.bot.say('No Open Matches found. Try again, {}.\nEnter `!matches` to view current matches.'.format(ctx.message.author.mention))
				return
			match = None
			for m in matches:
				if match_id and m.id==match_id:
					match = m
					break
				elif not match_id and m.contains_contestant(superstar):
					match = m
					team_id = m.team_by_contestant(superstar)
					break
				else:
					print('did not find {} in match {}'.format(superstar, m.id))
			if not match:
				await self.bot.say('Match not found. Try again, {}.\nEnter `!matches` to view current matches.'.format(ctx.message.author.mention))
				return
			if not match.bet_open:
				await self.bot.say('Match bets are closed. Try again, {}.\nEnter `!matches` to view current matches.'.format(ctx.message.author.mention))
				return
			team_members = match.contestants_by_team(team_id)
			if not team_members:
				await self.bot.say('Invalid Team. Try again, {}.'.format(ctx.message.author.mention))
				return
			ub = self.dbhandler.user_bet_check(user['id'], match.id)
			if ub:
				await self.bot.say('{}, you already have a {:,} bet placed on {}.'.format(ctx.message.author.mention, ub['points'], match.contestants_by_team(ub['team'])))
				return
			await self.bot.say('{}, are you sure you want to bet **{:,} points** on **{}**?  [Y/N]\n({})'.format(ctx.message.author.mention, bet, team_members, match.display_short()))
			confirm = await self.bot.wait_for_message(timeout=10.0, author=ctx.message.author, check=checks.confirm)
			if not confirm:
				await self.bot.say('You took too long to confirm. Try again, {}.'.format(ctx.message.author.mention))
			else:
				confirm.content = confirm.content.upper()
				if confirm.content=='Y':
					if self.dbhandler.user_bet(user['id'], match.id, team_id, bet):
						pot = self.dbhandler.match(match.id).base_pot
						await self.bot.say('{} placed a {:,} point bet on Match {} for **{}**!\nMatch Base Pot is now **{:,}** points.'.format(ctx.message.author.mention, bet, match.id, team_members, pot))
					else:
						await self.bot.say('{}, unable to process bet.'.format(ctx.message.author.mention))
				elif confirm.content=='N':
					await self.bot.say("{}'s bet cancelled. Coward.".format(ctx.message.author.mention))
		else:
			await self.bot.say('You are not registered.\nPlease visit http://matches.fancyjesse.com to register.\nThen link your Discord account by using command `!id`.')

	@commands.command(name='rate', pass_context=True)
	async def rate_match(self, ctx, *args):
		user = self.dbhandler.user_by_discord(ctx.message.author.id)
		if user:
			try:
				if self.bot.current_match:
					match_id = self.bot.current_match.id
					rate = float(args[0])
				else:
					match_id = int(args[0])
					rate = float(args[1])
			except:		
				await self.bot.say('Invalid `!rate` format.\n`!rate [match_id] [rating]`')
				return
			if rate<0 or rate>5:
				await self.bot.say('Invalid match rating. Try again, {}.'.format(ctx.message.author.mention))
				return
			m = self.dbhandler.match(match_id)
			if m:
				#if match['team_won']==0:
				#	await self.bot.say('Match rating unavailable - No decision yet, {}.'.format(ctx.message.author.mention))
				if (datetime.datetime.today().date() - m.date).days > 2:
					await self.bot.say('Match rating unavailable - Past 48 hours of event date, {}.'.format(ctx.message.author.mention))
				else:
					if not self.dbhandler.user_rate(user['id'], m.id, rate):
						await self.bot.say('Something went wrong. Try again later, {}.'.format(ctx.message.author.mention))
						return
					if rate:
						stars = ''
						for i in range(1,6):
							if rate>=i:
								stars += '★'
							else:
								stars += '☆'
						await self.bot.say('{0} gave `Match {1.id}` {2} ({3})'.format(ctx.message.author.mention, m, stars, rate))
					else:
						await self.bot.say('{0} removed their rating for `Match {1.id}`.'.format(ctx.message.author.mention, m))
			else:
				await self.bot.say('Match {} not found.'.format(match_id))
		else:
			await self.bot.say('You are not registered.\nPlease visit http://matches.fancyjesse.com to register.\nThen link your Discord account by using command `!id`.')

def setup(bot):
	bot.add_cog(Matches(bot))
