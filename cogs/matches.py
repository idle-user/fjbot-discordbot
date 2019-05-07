import asyncio
import datetime

from discord.ext import commands
import discord

from utils.dbhandler import DBHandler
from utils import checks, credentials, quickembed


class Matches(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		self.dbhandler = DBHandler()
		self.season = 3
		self.current_match = None
		self.bot.loop.create_task(self.showtime_schedule_task())

	async def showtime_schedule_task(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed():
			event = self.dbhandler.next_event()
			dt = datetime.datetime.now()
			timer = (event['date_time'] - dt).total_seconds()
			embed = quickembed.info(author=self.bot.user, desc='Event Notification')
			embed.add_field(name='{} has begun!'.format(event['name']), value='\u200b', inline=False)
			if event['ppv']:
				channel = self.bot.get_channel(credentials.discord['channel']['ppv'])
			elif 'RAW' in event['name']:
				channel = self.bot.get_channel(credentials.discord['channel']['raw'])
			elif 'SmackDown' in event['name']:
				channel = self.bot.get_channel(credentials.discord['channel']['sdlive'])
			else:
				channel = self.bot.get_channel(credentials.discord['channel']['general'])
			self.bot.log('showtime_schedule_task: channel={} sleep:{}'.format(channel.id, dt+datetime.timedelta(seconds=timer)), embed=embed)
			await asyncio.sleep(timer)
			if channel:
				await channel.send('everyone', embed=embed)
			break
		self.bot.log('END showtime_schedule_task')

	@commands.Cog.listener()
	async def on_member_join(self, member):
		channel = member.guild.system_channel
		role = self.bot.get_role(credentials.discord['role']['default'])
		await member.add_roles(role)
		await channel.send('Welcome to {}, {}! Say hi!'.format(member.guild.name, member.mention))

	@commands.command(name='ratestart')
	async def start_match_rating(self, ctx, match_id:str=None):
		await ctx.message.delete()
		owner = ctx.guild.get_member(credentials.discord['owner_id'])
		user = self.dbhandler.user_by_discord(ctx.author.id)
		if user.access<2:
			msg = '{}\n[#{}] {}: {}'.format('Invalid Command', ctx.message.channel, author, ctx.message.content)
			embed = quickembed.error(author=ctx.author, desc=msg, user=user)
			await owner.send(embed=embed)
			return

		try:
			if not match_id:
				match_id = self.dbhandler.latest_match()['id']
			match_id = int(match_id)
		except:
			msg = 'Invalid `!ratestart` format.'
			embed = quickembed.error(author=ctx.author, desc=msg, user=user)
			self.bot.log(embed=embed)
			return

		m = self.dbhandler.match(match_id)
		if m:
			msg = '```[Y/N]\nStart Rating on [{} | {}]?```'.format(m.match_type, m.contestants)
			message = await ctx.send(embed=quickembed.question(author=ctx.author, desc=msg, user=user))
			confirm = await self.bot.wait_for('message', check=checks.confirm, timeout=15.0)
			await message.delete()
			if not confirm:
				msg = '`!ratestart Match `{}` - Confirmation timeout'
				self.bot.log(embed=quickembed.error(author=ctx.author, desc=msg, user=user))
			else:
				await confirm.delete()
				confirm.content = confirm.content.upper()
				if confirm.content=='Y':
					self.current_match = m
					embed = discord.Embed(title='Match Rating has Begun!',
						url='https://fancyjesse.com/projects/matches/matches?match_id={}'.format(match_id),
						description='Use command `!rate [number]` to give a star rating.',
						color=0x0080ff)
					embed.add_field(name='Event', value=m.event, inline=True)
					if m.title:
						embed.add_field(name='Title', value=m.title, inline=True)
					embed.add_field(name='Type', value=m.match_type, inline=True)
					embed.add_field(name='Contestants', value=m.contestants, inline=True)
					embed.add_field(name='Winner(s)', value=m.contestants_won, inline=True)
					self.bot.log('!ratestart ({})'.format(ctx.author.name), embed=embed)
					await ctx.send(embed=embed)
				else:
					msg = '`!ratestart` Match `{}` - Cancelled'.format(match_id)
					self.bot.log(embed=quickembed.error(author=ctx.author, desc=msg, user=user))
		else:
			msg = '`!ratestart` Match `{}` not found'.format(match_id)
			self.bot.log(embed=quickembed.error(author=ctx.author, desc=msg, user=user))

	@commands.command(name='rateend')
	async def end_match_rating(self, ctx):
		await ctx.message.delete()
		user = self.dbhandler.user_by_discord(ctx.author.id)
		if user.access<2:
			msg = '!rateend - Insufficient access'
			self.bot.log(embed=quickembed.general(author=ctx.author, desc=msg))
			return
		if self.current_match:
			match_id = self.current_match.id
			self.current_match = {}
			m = self.dbhandler.match(match_id)
			msg = 'Match Rating has ended.\nReceived a total of {0.star_rating} ({0.user_rating_avg:.3f}).\n[{0.match_type} | {0.contestants}]'.format(m)
			await ctx.send(embed=quickembed.general(author=ctx.author, desc=msg))
		else:
			msg = '!rateend - No current match set.'
			self.bot.log(embed=quickembed.general(author=ctx.author, desc=msg))

	@commands.command(name='id')
	async def send_userid(self, ctx):
		await ctx.message.delete()
		msg = 'Your discord_id is: `{}`\nLink it to your http://matches.fancyjesse.com profile.'.format(ctx.author.id)
		embed = quickembed.general(author=ctx.author, desc=msg)
		await ctx.author.send(embed=embed)

	@commands.command(name='register', aliases=['verify'])
	async def register_user(self, ctx):
		user = self.dbhandler.user_by_discord(ctx.author.id)
		if user:
			msg = 'Your Discord is already registed.'
			embed = quickembed.success(author=ctx.author, desc=msg, user=user)
			await ctx.send(embed=embed)
		else:
			msg = '[Y/N]\nYour Discord is not linked to an existing Matches account (http://matches.fancyjesse.com)\nWould you like to continue registering a new account?'
			embed = quickembed.question(author=ctx.author, desc=msg)
			await ctx.send(embed=embed)
			confirm = await self.bot.wait_for('message', check=checks.confirm, timeout=15.0)
			if not confirm:
				msg = 'You took too long to confirm. Try again.'
				embed = quickembed.error(author=ctx.author, desc=msg)
				await ctx.send(embed=embed)
				self.bot.log(embed=embed)
			else:
				confirm.content = confirm.content.upper()
				if confirm.content=='Y':
					user = self.dbhandler.discord_register(ctx.author.id)
					if user:
						msg = 'Successfully registered.\nPlease contact an admin to request a one-time username change.'
						embed = quickembed.success(author=ctx.author, desc=msg, user=user)
						await ctx.send(embed=embed)
						self.bot.log(embed=embed)
					else:
						msg = 'Failed to register. Please contact an admin.'
						embed = quickembed.error(author=ctx.author, desc=msg)
						await ctx.send(embed=embed)
						self.bot.log(embed=embed)
				elif confirm.content=='N':
					await ctx.send('Account registration cancelled.')

	@commands.command(name='login')
	async def user_quick_login(self, ctx):
		user = self.dbhandler.user_by_discord(ctx.author.id)
		if user:
			await ctx.message.delete()
			token = self.bot.dbhandler.user_login_token(user.id)
			link = 'https://fancyjesse.com/projects/matches?uid={}&token={}'.format(user.id, token)
			msg = 'Quick login link for you! (link expires in 5 minutes)\n<{}>'.format(link)
			embed = quickembed.general(author=ctx.author, desc=msg, user=user)
			await ctx.author.send(embed=embed)
		else:
			await ctx.send('Your Discord is not linked to an existing Matches account.\nUse `!register` or visit http://matches.fancyjesse.com to link your existing account.')

	@commands.command(name='events', aliases=['ppv','ppvs'])
	async def upcomming_events(self, ctx):
		ppvs = self.dbhandler.events()
		embed = quickembed.info(author=self.bot.user, desc='Upcoming Events (PT)')
		embed.add_field(name='\u200b', value='\n'.join(['{} - **{}**'.format(e['date_time'],e['name']) for e in ppvs]))
		await ctx.send(embed=embed)

	@commands.command(name='info', aliases=['bio', 'superstar'])
	async def superstar_info(self, ctx, *, content:str):
		superstar_list = self.dbhandler.superstar_search('%{}%'.format(content.replace(' ','%')))
		if not superstar_list:
			await ctx.send("Unable to find Superstars matching '{}'".format(content))
			return
		else:
			if len(superstar_list)>1:
				msg = 'Select Superstar from List ...\n```'
				for i,e in enumerate(superstar_list):
					msg = msg + '{}. {}\n'.format(i+1, e.name)
				msg = msg + '```'
				await ctx.send(msg)
				response = await self.bot.wait_for_message(timeout=15.0, author=ctx.author, check=checks.is_number)
				if not response:
					await ctx.send('You took too long to confirm. Try again, {}.'.format(ctx.author.mention))
				else:
					try:
						index = int(response.content)
						superstar = superstar_list[index-1]
					except:
						await ctx.send('Invalid Index.')
						return
			else:
				superstar = superstar_list[0]

			await ctx.send(embed=superstar.info_embed())

	@commands.command(name='birthdays')
	async def superstar_birthdays(self, ctx):
		bdays = self.dbhandler.superstar_birthdays()
		await ctx.send('```Birthdays This Month\n-------------\n{}```'.format('\n'.join(['[{}] {}'.format(b['dob'],b['name']) for b in bdays])))

	@commands.command(name='superstars', aliases=['superstarlist', 'listsuperstars'])
	async def all_superstars(self, ctx):
		sl = self.dbhandler.superstars()
		sl = [s.name for s in sl]
		await ctx.send('```{}```'.format('\n'.join(sl)))

	@commands.command(name='leaderboard_s1', aliases=['top1'])
	async def leaderboard_season1(self, ctx):
		lb = self.dbhandler.leaderboard_s1()
		embed = discord.Embed(title='Leaderboard',
			url='https://fancyjesse.com/projects/matches/leaderboard?season_id=1',
			description='Season 1',
			color=0x0080ff)
		lb = ['{}. {} ({:,})'.format(i+1,l['username'],l['s1_total_points']) for i, l in enumerate(lb)]
		embed.add_field(name='Rankings', value='\n'.join(lb) if lb else 'Nothing found', inline=True)
		await ctx.send(embed=embed)

	@commands.command(name='leaderboard_s2', aliases=['top2'])
	async def leaderboard_season2(self, ctx):
		lb = self.dbhandler.leaderboard_s2()
		embed = discord.Embed(title='Leaderboard',
			url='https://fancyjesse.com/projects/matches/leaderboard?season_id=2',
			description='Season 2',
			color=0x0080ff)
		lb = ['{}. {} ({:,})'.format(i+1,l['username'],l['s2_total_points']) for i, l in enumerate(lb)]
		embed.add_field(name='Rankings', value='\n'.join(lb) if lb else 'Nothing found', inline=True)
		await ctx.send(embed=embed)

	@commands.command(name='leaderboard_s3', aliases=['top', 'leaderboard', 'top3'])
	async def leaderboard_season3(self, ctx):
		lb = self.dbhandler.leaderboard_s3()
		embed = discord.Embed(title='Leaderboard',
			url='https://fancyjesse.com/projects/matches/leaderboard?season_id=3',
			description='Season 3',
			color=0x0080ff)
		lb = ['{}. {} ({:,})'.format(i+1,l['username'],l['s3_total_points']) for i, l in enumerate(lb)]
		embed.add_field(name='Rankings', value='\n'.join(lb) if lb else 'Nothing found', inline=True)
		await ctx.send(embed=embed)

	@commands.command(name='titles', aliases=['champions','champs'])
	async def current_champions(self, ctx):
		ts = self.dbhandler.titles()
		embed = discord.Embed(title='Current Champions',
			url='https://fancyjesse.com/projects/matches/champions',
			description='',
			color=0x0080ff)
		for t in ts:
			embed.add_field(name=t['title'], value=t['superstar'], inline=False)
		await ctx.send(embed=embed)

	@commands.command(name='rumble')
	async def rumble_info(self, ctx):
		await ctx.send('Join the Rumble at: https://fancyjesse.com/projects/matches/royalrumble')
		user = self.dbhandler.user_by_discord(ctx.author.id)
		if user:
			token = self.bot.dbhandler.user_login_token(user.id)
			link = 'https://fancyjesse.com/projects/matches/royalrumble?uid={}&token={}'.format(user.id, token)
			await ctx.author.send('Quick login link for you! <{}> (link expires in 5 minutes)'.format(link))
		else:
			await ctx.send('Your Discord is not linked to an existing Matches account.\nUse `!register` or visit http://matches.fancyjesse.com to link your existing account.')

	@commands.command(name='stats_s3', aliases=['stats', 'balance', 'bal', 'points', 'wins', 'losses', 'profile', 'mypage', 's3stats', 's3_stats'])
	async def user_stats_season3(self, ctx):
		user = self.dbhandler.user_by_discord(ctx.author.id)
		if user:
			season = 3
			user = self.dbhandler.user_stats(user.id)
			await ctx.send(embed=user.stats_embed(author=ctx.author, season=season))
		else:
			await ctx.send('Your Discord is not linked to an existing Matches account.\nUse `!register` or visit http://matches.fancyjesse.com to link your existing account.')

	@commands.command(name='stats_s2', aliases=['s2stats', 's2_stats'])
	async def user_stats_season2(self, ctx):
		user = self.dbhandler.user_by_discord(ctx.author.id)
		if user:
			season = 2
			user = self.dbhandler.user_stats(user.id)
			await ctx.send(embed=user.stats_embed(author=ctx.author, season=season))
		else:
			await ctx.send('Your Discord is not linked to an existing Matches account.\nUse `!register` or visit http://matches.fancyjesse.com to link your existing account.')

	@commands.command(name='stats_s1', aliases=['s1stats', 's1_stats'])
	async def user_stats_season1(self, ctx):
		user = self.dbhandler.user_by_discord(ctx.author.id)
		if user:
			season = 1
			user = self.dbhandler.user_stats(user.id)
			await ctx.send(embed=user.stats_embed(author=ctx.author, season=season))
		else:
			await ctx.send('Your Discord is not linked to an existing Matches account.\nUse `!register` or visit http://matches.fancyjesse.com to link your existing account.')

	@commands.command(name='bets', aliases=['currentbets'])
	async def user_current_bets(self, ctx):
		user = self.dbhandler.user_by_discord(ctx.author.id)
		if user:
			bets = self.dbhandler.user_bets(user.id)
			if bets:
				await ctx.send("{}'s Current Bets\n```{}```".format(ctx.author.mention, '\n'.join(['Match {}\n  {:,} points on {}\n  Potential Pot Winnings: {:,} ({}%)'.format(bet['match_id'], bet['points'], bet['contestants'], bet['potential_cut_points'], bet['potential_cut_pct']*100) for bet in bets])))
			else:
				await ctx.send('{} has no bets placed on Matches.'.format(ctx.author.mention))
		else:
			await ctx.send('Your Discord is not linked to an existing Matches account.\nUse `!register` or visit http://matches.fancyjesse.com to link your existing account.')

	@commands.command(name='match')
	async def match_info(self, ctx, id=None):
		try:
			match_id = int(id)
		except:
			await ctx.send('Invalid `!match` format.\n`!match [match_id]`')
			return
		m = self.dbhandler.match(match_id)
		if m:
			await ctx.send(embed=m.info_embed())
		else:
			msg = 'Match `{}` not found.'.format(match_id)
			await ctx.send(embed=quickembed.error(author=ctx.author, desc=msg))

	@commands.command(name='matches', aliases=['openmatches'])
	async def open_matches(self, ctx):
		match_list = self.dbhandler.open_matches()
		if match_list:
			for m in match_list:
				await ctx.send(embed=m.info_embed())
		else:
			msg = 'No open bet matches available.'
			embed = quickembed.error(author=ctx.author, desc=msg)
			await ctx.send(embed=embed)

	@commands.command(name='bet')
	async def place_match_bet(self, ctx, *args):
		user = self.dbhandler.user_by_discord(ctx.author.id)
		if user:
			try:
				bet = int(args[0].replace(',',''))
				if len(args)==3 and args[1].isdigit() and args[2].isdigit():
					match_id = int(args[1])
					team_id = int(args[2])
					superstar = False
				else:
					superstar = ' '.join(args[1:])
					match_id = False
			except:
				msg = 'Invalid `!bet` format.\n`!bet [bet_amount] [contestant]`\n`!bet [bet_amount] [match_id] [team]`'
				embed = quickembed.error(author=ctx.author, desc=msg, user=user)
				await ctx.send(embed=embed)
				return
			if bet<1:
				msg = 'Invalid bet. Try again.'
				embed = quickembed.error(author=ctx.author, desc=msg, user=user)
				await ctx.send(embed=embed)
				return
			user = self.dbhandler.user_stats(user.id)
			if user.season_available_points(self.season) < bet:
				msg = 'Insufficient points available: `({})`. Try again.'.format(user.season_available_points(self.season))
				embed = quickembed.error(author=ctx.author, desc=msg, user=user)
				await ctx.send(embed=embed)
				return
			matches = self.dbhandler.open_matches()
			if not matches:
				msg = 'No Open Matches found. Try again.\n`!matches` to view current matches.'
				embed = quickembed.error(author=ctx.author, desc=msg, user=user)
				await ctx.send(embed=embed)
				return
			match = None
			for m in matches:
				if match_id and m.id==match_id:
					match = m
					break
				elif superstar and m.contains_contestant(superstar):
					match = m
					team_id = m.team_by_contestant(superstar)
					break
			if not match:
				msg = 'Match not found. Try again.\n`!matches` to view current matches.'
				embed = quickembed.error(author=ctx.author, desc=msg, user=user)
				await ctx.send(embed=embed)
				return
			if not match.bet_open:
				msg = 'Match bets are closed. Try again.\n`!matches` to view current matches.'
				return
			team_members = match.contestants_by_team(team_id)
			if not team_members:
				msg = 'Invalid Team. Try again.'
				embed = quickembed.error(author=ctx.author, desc=msg, user=user)
				await ctx.send(embed=embed)
				return
			ub = self.dbhandler.user_bet_check(user.id, match.id)
			if ub:
				msg = 'You already have a `{:,}` bet placed on `{}`.'.format(ub['points'], match.contestants_by_team(ub['team']))
				embed = quickembed.error(author=ctx.author, desc=msg, user=user)
				await ctx.send(embed=embed)
				return
			msg = '[Y/N]\nAre you sure you want to bet `{:,}` points on `{}`?\n({})'.format(bet, team_members, match.display_short())
			embed = quickembed.question(author=ctx.author, desc=msg, user=user)
			await ctx.send(embed=embed)
			confirm = await self.bot.wait_for('message', check=checks.confirm, timeout=10.0)
			if not confirm:
				msg = 'You took too long to confirm. Try again.'
				embed = quickembed.error(author=ctx.author, desc=msg, user=user)
				await ctx.send(embed=embed)
			else:
				confirm.content = confirm.content.upper()
				if confirm.content=='Y':
					if self.dbhandler.user_bet(user.id, match.id, team_id, bet):
						pot = self.dbhandler.match(match.id).base_pot
						msg = 'Placed a `{:,}` point bet on Match `{}` for `{}`!\nMatch Base Pot is now `{:,}` points.'.format(bet, match.id, team_members, pot)
						embed = quickembed.success(author=ctx.author, desc=msg, user=user)
						await ctx.send(embed=embed)
					else:
						msg = '{}, unable to process bet.'.format(ctx.author.mention)
						embed = quickembed.error(author=ctx.author, desc=msg, user=user)
						await ctx.send(embed=embed)
				elif confirm.content=='N':
					msg = 'Bet cancelled. Coward.'
					embed = quickembed.error(author=ctx.author, desc=msg, user=user)
					await ctx.send(embed=embed)
		else:
			msg = 'Your Discord is not linked to an existing Matches account.\nUse `!register` or visit http://matches.fancyjesse.com to link your existing account.'
			embed = quickembed.error(author=ctx.author, desc=msg)
			await ctx.send(embed=embed)

	@commands.command(name='rate')
	async def rate_match(self, ctx, *args):
		user = self.dbhandler.user_by_discord(ctx.author.id)
		if user:
			try:
				if self.current_match:
					match_id = self.current_match.id
					rate = float(args[0])
				else:
					match_id = int(args[0])
					rate = float(args[1])
			except:
				msg = 'Invalid `!rate` format.\n`!rate [match_id] [rating]`'
				embed = quickembed.error(author=ctx.author, desc=msg, user=user)
				await ctx.send(embed=embed)
				return
			if rate<=0 or rate>5:
				msg = 'Invalid match rating. Try again.'
				embed = quickembed.error(author=ctx.author, desc=msg, user=user)
				await ctx.send(embed=embed)
				return
			m = self.dbhandler.match(match_id)
			if m:
				if (datetime.datetime.today().date() - m.date).days > 2:
					msg = 'Match rating unavailable - Past 48 hours of event date'
					embed = quickembed.error(author=ctx.author, desc=msg, user=user)
					await ctx.send(embed=embed)
				else:
					if not self.dbhandler.user_rate(user.id, m.id, rate):
						msg = 'Something went wrong. Try again later.'
						embed = quickembed.error(author=ctx.author, desc=msg, user=user)
						await ctx.send(embed=embed)
						return
					if rate:
						stars = ''
						for i in range(1,6):
							if rate>=i:
								stars += '★'
							else:
								stars += '☆'
						msg = 'Rated `Match {}` {} ({})'.format(m.id, stars, rate)
						embed = quickembed.success(author=ctx.author, desc=msg, user=user)
						await ctx.send(embed=embed)
			else:
				msg = 'Match {} not found.'.format(match_id)
				embed = quickembed.error(author=ctx.author, desc=msg, user=user)
				await ctx.send(embed=embed)
		else:
			msg = 'Your Discord is not linked to an existing Matches account.\nUse `!register` or visit http://matches.fancyjesse.com to link your existing account.'
			embed = quickembed.error(author=ctx.author, desc=msg, user=user)
			await ctx.send(embed=embed)

def setup(bot):
	bot.add_cog(Matches(bot))
