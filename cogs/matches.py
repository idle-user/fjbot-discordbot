import asyncio
import datetime

from discord.ext import commands
import discord

from utils.fjclasses import _DbHelper, DiscordUser, Superstar, Match
from utils import config, checks, quickembed


class Matches(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.current_match = None
		self.bot.loop.create_task(self.showtime_schedule_task())

	async def showtime_schedule_task(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed():
			event = _DbHelper().future_events()[0]
			dt = datetime.datetime.now()
			event_start_timer = (event['date_time'] - dt).total_seconds()
			embed = quickembed.info(desc='Event')
			embed.add_field(name='{} has begun!'.format(event['name']), value='\u200b', inline=False)
			event_length_timer = 14400
			if event['ppv']:
				channel = self.bot.get_channel(config.discord['channel']['ppv'])
			elif 'RAW' in event['name']:
				channel = self.bot.get_channel(config.discord['channel']['raw'])
				event_length_timer = 10800
			elif 'SmackDown' in event['name']:
				channel = self.bot.get_channel(config.discord['channel']['sdlive'])
				event_length_timer = 7200
			else:
				channel = self.bot.get_channel(config.discord['channel']['general'])
			self.bot.log(content='```\nshowtime_schedule_task\nchannel: `{}`\nsleep until: `{}`\n```'.format(channel.name, dt+datetime.timedelta(seconds=event_start_timer)), embed=embed)
			await asyncio.sleep(event_start_timer)
			if channel:
				await channel.send('@everyone', embed=embed)
				activity = discord.Activity(type=discord.ActivityType.watching, name=event['name'])
				await self.bot.change_presence(activity=activity)
				await asyncio.sleep(event_length_timer)
		self.bot.log('```\nshowtime_schedule_task\nEND\n```')

	@commands.Cog.listener()
	async def on_member_join(self, member):
		channel = member.guild.system_channel
		role = self.bot.get_role(config.discord['role']['default'])
		await member.add_roles(role)
		await channel.send('Welcome to {}, {}! Say hi!'.format(member.guild.name, member.mention))

	@commands.command(name='ratestart')
	@commands.has_any_role(config.discord['role']['admin'], config.discord['role']['mod'])
	async def start_match_rating(self, ctx, match_id:str=None):
		owner = ctx.guild.get_member(config.discord['owner_id'])
		user = DiscordUser(ctx.author)
		if user.access<2:
			msg = '{}\n[#{}] {}: {}'.format('Invalid Command', ctx.channel, ctx.author, ctx.content)
			embed = quickembed.error(desc=msg, user=user)
			await owner.send(embed=embed)
			return

		try:
			if not match_id:
				match_id = self.dbhandler.latest_match()['id']
			match_id = int(match_id)
		except:
			msg = 'Invalid `!ratestart` format.'
			embed = quickembed.error(desc=msg, user=user)
			self.bot.log(embed=embed)
			return

		m = self.dbhandler.match(match_id)
		if m:
			msg = '```[Y/N]\nStart Rating on [{} | {}]?```'.format(m.match_type, m.contestants)
			message = await ctx.send(embed=quickembed.question(desc=msg, user=user))
			confirm = await self.bot.wait_for('message', check=checks.confirm(ctx.author), timeout=15.0)
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
				self.bot.log(embed=quickembed.error(desc=msg, user=user))
		else:
			msg = '`!ratestart` Match `{}` not found'.format(match_id)
			self.bot.log(embed=quickembed.error(desc=msg, user=user))

	@commands.command(name='rateend')
	@commands.has_any_role(config.discord['role']['admin'], config.discord['role']['mod'])
	async def end_match_rating(self, ctx):
		user = DiscordUser(ctx.author)
		if user.access<2:
			msg = '!rateend - Insufficient access'
			self.bot.log(embed=quickembed.general(desc=msg, user=user))
			return
		if self.current_match:
			match_id = self.current_match.id
			self.current_match = {}
			m = self.dbhandler.match(match_id)
			msg = 'Match Rating has ended.\nReceived a total of {0.star_rating} ({0.user_rating_avg:.3f}).\n[{0.match_type} | {0.contestants}]'.format(m)
			await ctx.send(embed=quickembed.general(desc=msg, user=user))
		else:
			msg = '!rateend - No current match set.'
			self.bot.log(embed=quickembed.general(desc=msg, user=user))

	@commands.command(name='id')
	async def send_userid(self, ctx):
		user = DiscordUser(ctx.author)
		msg = 'Your discord_id is: `{}`\nLink it to your http://matches.fancyjesse.com profile.'.format(user.discord.id)
		embed = quickembed.general(desc=msg, user=user)
		await ctx.author.send(embed=embed)
		await ctx.send(embed=quickembed.general(desc='Information DMed', user=user))

	@commands.command(name='register', aliases=['verify'])
	async def register_user(self, ctx):
		user = DiscordUser(ctx.author)
		if user.is_registered():
			embed = quickembed.success(user=user, desc='Your Discord is already registered')
		else:
			textquestion = '[Y/N]\nYour Discord is not linked to an existing Matches account (http://matches.fancyjesse.com)\nWould you like to register a new account?'
			embedquestion = quickembed.question(user=user, desc=textquestion)
			await ctx.send(embed=embedquestion)
			confirm = await self.bot.wait_for('message', check=checks.confirm(ctx.author), timeout=15.0)
			confirm.content = confirm.content.upper()
			if confirm.content=='Y':
				response = user.register()
				if response['success']:
					embed = quickembed.success(user=user, desc='Successfully registered.\nPlease contact an admin to request a one-time username change.')
				else:
					embed = quickembed.error(user=user, desc='Failed to register.\nPlease contact an admin.')
			elif confirm.content=='N':
				embed=quickembed.error(user=user, desc='Account registration cancelled')
		await ctx.send(embed=embed)
		self.bot.log(embed=embed)

	@commands.command(name='login')
	@checks.is_registered()
	async def user_quick_login(self, ctx):
		user = DiscordUser(ctx.author)
		link = user.request_login_link()
		msg = 'Quick login link for you! (link expires in 5 minutes)\n<{}>'.format(link)
		await ctx.author.send(embed=quickembed.general(desc=msg, user=user))
		embed=quickembed.success(user=user, desc='Login link DMed')
		await ctx.send(embed=embed)

	@commands.command(name='events', aliases=['ppv','ppvs'])
	async def upcomming_events(self, ctx):
		user = DiscordUser(ctx.author)
		ppvs = user.future_events(ppv_check=1)
		embed = quickembed.info(desc='Upcoming Events (PT)', user=user)
		embed.add_field(name='\u200b', value='\n'.join(['{} - **{}**'.format(e['date_time'],e['name']) for e in ppvs]))
		await ctx.send(embed=embed)

	@commands.command(name='info', aliases=['bio', 'superstar'])
	async def superstar_info(self, ctx, *, name):
		user = DiscordUser(ctx.author)
		superstar_list = user.search_superstar_by_name(name)
		if not superstar_list:
			embed = quickembed.error(desc="Unable to find Superstars matching '{}'".format(name), user=user)
		else:
			if len(superstar_list)>1:
				msg = 'Select Superstar from List ...\n```'
				for i,e in enumerate(superstar_list):
					msg = msg + '{}. {}\n'.format(i+1, e.name)
				msg = msg + '```'
				await ctx.send(embed=quickembed.question(desc=msg,  user=user))
				response = await self.bot.wait_for('message', check=checks.is_number(ctx.author), timeout=15.0)
				try:
					index = int(response.content)
					embed = Superstar(superstar_list[index-1].id).info_embed()
				except:
					embed = quickembed.error(desc='Invalid index', user=user)
			else:
				embed = Superstar(superstar_list[0].id).info_embed()	
		await ctx.send(embed=embed)

	@commands.command(name='birthdays')
	async def superstar_birthdays(self, ctx):
		user = DiscordUser(ctx.author)
		bdays = user.superstar_birthday_upcoming()
		embed = quickembed.info(desc='Upcoming Birthdays', user=user)
		embed.add_field(name='\u200b', value='{}'.format('\n'.join(['[{}] - {}'.format(b['dob'],b['name']) for b in bdays])))
		await ctx.send(embed=embed)

	@commands.command(name='leaderboard_s1', aliases=['top1'])
	async def leaderboard_season1(self, ctx):
		user = DiscordUser(ctx.author)
		lb = user.leaderboard(season=1)
		embed = discord.Embed(description='Season 1', color=0x0080ff)
		embed.set_author(
			name='Leaderboard',
			url='https://fancyjesse.com/projects/matches/leaderboard?season_id=1',
			icon_url=self.bot.user.avatar_url)
		lb = ['{}. {} ({:,})'.format(i+1,l['username'],l['total_points']) for i, l in enumerate(lb[:10])]
		embed.add_field(name='\u200b', value='\n'.join(lb) if lb else 'Nothing found', inline=True)
		await ctx.send(embed=embed)

	@commands.command(name='leaderboard_s2', aliases=['top2'])
	async def leaderboard_season2(self, ctx):
		user = DiscordUser(ctx.author)
		lb = user.leaderboard(season=2)
		embed = discord.Embed(description='Season 2', color=0x0080ff)
		embed.set_author(
			name='Leaderboard',
			url='https://fancyjesse.com/projects/matches/leaderboard?season_id=2',
			icon_url=self.bot.user.avatar_url)
		lb = ['{}. {} ({:,})'.format(i+1,l['username'],l['total_points']) for i, l in enumerate(lb[:10])]
		embed.add_field(name='\u200b', value='\n'.join(lb) if lb else 'Nothing found', inline=True)
		await ctx.send(embed=embed)

	@commands.command(name='leaderboard_s3', aliases=['top', 'leaderboard', 'top3'])
	async def leaderboard_season3(self, ctx):
		user = DiscordUser(ctx.author)
		lb = user.leaderboard(season=3)
		embed = discord.Embed(description='Season 3', color=0x0080ff)
		embed.set_author(
			name='Leaderboard',
			url='https://fancyjesse.com/projects/matches/leaderboard?season_id=3',
			icon_url=self.bot.user.avatar_url)
		lb = ['{}. {} ({:,})'.format(i+1,l['username'],l['total_points']) for i, l in enumerate(lb[:10])]
		embed.add_field(name='\u200b', value='\n'.join(lb) if lb else 'Nothing found', inline=True)
		await ctx.send(embed=embed)

	# TODO
	@commands.command(name='titles', aliases=['champions','champs'])
	async def current_champions(self, ctx):
		user = DiscordUser(ctx.author)
		ts = self.dbhandler.titles()
		embed = discord.Embed(title='Current Champions',
			url='https://fancyjesse.com/projects/matches/champions',
			description='',
			color=0x0080ff)
		for t in ts:
			embed.add_field(name=t['title'], value=t['superstar'], inline=False)
		await ctx.send(embed=embed)

	# TODO
	@commands.command(name='rumble')
	@commands.is_owner()
	async def rumble_info(self, ctx):
		await ctx.send('Join the Rumble at: https://fancyjesse.com/projects/matches/royalrumble')
		user = DiscordUser(ctx.author)
		if user:
			token = self.bot.dbhandler.user_login_token(user.id)
			link = 'https://fancyjesse.com/projects/matches/royalrumble?uid={}&token={}'.format(user.id, token)
			await ctx.author.send('Quick login link for you! <{}> (link expires in 5 minutes)'.format(link))
		else:
			msg = 'Your Discord is not linked to an existing Matches account.\nUse `!register` or visit http://matches.fancyjesse.com to link to your existing account.'
			await ctx.send(embed=quickembed.error(desc=msg, user=user))

	@commands.command(name='stats3', aliases=['stats', 'balance', 'bal', 'points', 'wins', 'losses', 'profile', 'mypage', 's3stats'])
	@checks.is_registered()
	async def user_stats_season3(self, ctx):
		await ctx.send(embed=DiscordUser(ctx.author).stats_embed(season=3))

	@commands.command(name='stats2', aliases=['s2stats'])
	@checks.is_registered()
	async def user_stats_season2(self, ctx):
		await ctx.send(embed=DiscordUser(ctx.author).stats_embed(season=2))

	@commands.command(name='stats1', aliases=['s1stats'])
	@checks.is_registered()
	async def user_stats_season1(self, ctx):
		await ctx.send(embed=DiscordUser(ctx.author).stats_embed(season=1))

	@commands.command(name='bets', aliases=['currentbets'])
	@checks.is_registered()
	async def user_current_bets(self, ctx):
		user = DiscordUser(ctx.author)
		bets = user.current_bets()
		if bets:
			msg = "```{}```".format('\n'.join(['Match {}\n\t{:,} points on {}\n\tPotential Winnings: {:,} ({}%)'.format(bet['match_id'], bet['points'], bet['contestants'], bet['potential_cut_points'], bet['potential_cut_pct']*100) for bet in bets]))
			embed = quickembed.general(desc='Current Bets', user=user)
			embed.add_field(name='\u200b', value=msg, inline=False)
		else:
			embed = quickembed.error(desc='No current bets placed', user=user)
		await ctx.send(embed=embed)

	@commands.command(name='match')
	async def match_info(self, ctx, id=None):
		user = DiscordUser(ctx.author)
		try:
			match_id = int(id)
		except:
			msg = 'Invalid `!match` format.\n`!match [match_id]`'
			await ctx.send(embed=quickembed.error(desc=msg, user=user))
			return
		rows = user.search_match_by_id(id)
		if rows:
			await ctx.send(embed=Match(rows[0].id).info_embed())
		else:
			await ctx.send(embed=quickembed.error(desc='Match `{}` not found'.format(match_id), user=user))

	@commands.command(name='matches', aliases=['openmatches'])
	async def open_matches(self, ctx):
		user = DiscordUser(ctx.author)
		rows = user.search_match_by_open_bets()
		if rows:
			for row in rows:
				await ctx.send(embed=Match(row.id).info_embed())
		else:
			await ctx.send(embed=quickembed.error(desc='No open bet matches available', user=user))

	@commands.command(name='bet', aliases=['placebet'])
	@checks.is_registered()
	async def place_match_bet(self, ctx, *args):
		user = DiscordUser(ctx.author)
		try:
			bet = int(args[0].replace(',',''))
			if len(args)==3 and args[1].isdigit() and args[2].isdigit():
				match_id = int(args[1])
				team = int(args[2])
				superstar = False
			else:
				superstar = ' '.join(args[1:])
				match_id = False
				rows = user.search_match_by_open_bets_and_supertar_name(superstar)
				match_id = rows[0] if rows else False
				if not match_id:
					embed = quickembed.error('Unable to find an open match for `{}`'.format(superstar), user=user)
					return
		except:
			msg = 'Invalid `!bet` format.\n`!bet [bet_amount] [contestant]`\n`!bet [bet_amount] [match_id] [team]`'
			embed = quickembed.error(desc=msg, user=user)
			await ctx.send(embed=embed)
			return
		response = user.validate_bet(match_id, team, bet)
		if response['success']:
			embedquestion = quickembed.question(desc='[Y/N] Place this bet?', user=user)
			embedquestion.add_field(name='Info', value=match.info_text_short(), inline=False)
			embedquestion.add_field(name='Betting', value=bet, inline=True)
			embedquestion.add_field(name='Betting On', value=match.teams[team]['members'], inline=True)
			await ctx.send(embed=embedquestion)
			confirm = await self.bot.wait_for('message', check=checks.confirm(ctx.author), timeout=15.0)
			confirm.content = confirm.content.upper()
			if confirm.content=='Y':
				response = user.place_bet(match_id, team, bet)
				if response['success']:
					embed = quickembed.success(desc=response['message'], user=user)
				else:
					embed = quickembed.error(desc=response['message'], user=user)
			elif confirm.content=='N':
				embed = quickembed.error(desc='Bet cancelled', user=user)
		else:
			embed = quickembed.error(desc=response['message'], user=user)

		await ctx.send(embed=embed)

	@commands.command(name='rate', aliases=['ratematch'])
	@checks.is_registered()
	async def rate_match(self, ctx, *args):
		user = DiscordUser(ctx.author)
		try:
			if self.current_match:
				match_id = self.current_match.id
				rating = float(args[0])
			else:
				match_id = int(args[0])
				rating = float(args[1])
		except:
			msg = 'Invalid `!rate` format.\n`!rate [match_id] [rating]`'
			embed = quickembed.error(desc=msg, user=user)
			await ctx.send(embed=embed)
			return
		response = user.rate_match(match_id, rating)
		if response['success']:
			stars = ''
			for i in range(1,6):
				if rating>=i:
					stars += '★'
				else:
					stars += '☆'
			msg = 'Rated `Match {}` {} ({})'.format(match_id, stars, rating)
			embed = quickembed.success(desc=msg, user=user)
		else:
			msg = response['message']
			embed = quickembed.error(desc=msg, user=user)
		await ctx.send(embed=embed)

def setup(bot):
	bot.add_cog(Matches(bot))
