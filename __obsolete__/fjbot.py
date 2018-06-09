#!/usr/bin/env python3
import datetime
import asyncio
import random

from discord.ext import commands
import discord


from dbhandler import DBHandler
import credentials
import twitter
import chatango


dbhandler = DBHandler()

bot = commands.Bot(command_prefix='!', description='FJBot is a Discord Bot written in Python by FancyJesse')
discord_ad = 'Join the WWE Chat Discord for a better chat experience. Uncensored Chat, Organized Topics, and WWE gifs and emojis! https://discord.gg/Q9mX5hQ'
channel_debug = discord.Object(id=credentials.discord['channel']['debug'])
channel_general = discord.Object(id=credentials.discord['channel']['general'])
channel_ppv = discord.Object(id=credentials.discord['channel']['ppv'])
channel_raw = discord.Object(id=credentials.discord['channel']['raw'])
channel_sd = discord.Object(id=credentials.discord['channel']['sdlive'])
channel_twitter = discord.Object(id=credentials.discord['channel']['twitter'])
channel_chatango = discord.Object(id=credentials.discord['channel']['chatango'])

current_match = {}

def confirm_check(m):
	return m.content.upper() in ['Y','N']

# debug
async def debug(message):
	message = '[{}] {}'.format(datetime.datetime.now().replace(microsecond=0), message)
	print(message)
	if not bot.is_closed:
		pass
		await bot.send_message(channel_debug, message)

@bot.event
async def on_command_error(error, ctx):
	return
	if 'is not found' in str(error):
		return
	if ctx.message.channel.is_private:
		await bot.send_message(ctx.message.channel, "Stop trying to command me privately. I'm not into BDSM, you creep.")
	else:
		owner = ctx.message.server.get_member(credentials.discord['owner_id'])
		if owner:
			await bot.send_message(owner, '```{}\n[#{}] {}: {}```'.format(error, ctx.message.channel, ctx.message.author, ctx.message.content))
		raise error

# async tasks
async def showtime_schedule_task():
	await bot.wait_until_ready()
	await debug('showtime_schedule_task: START')
	while not bot.is_closed:
		event = dbhandler.next_event()
		dt = datetime.datetime.now()
		timer = (event['dt'] - dt).total_seconds()
		await debug('showtime_schedule_task: sleep:{}, until:{}, event:{}'.format(timer, dt+datetime.timedelta(seconds=timer), event['name']))
		await asyncio.sleep(timer)
		if 'RAW' in event['name']:
			await bot.send_message(channel_raw, "@everyone, it's time for **Monday Night RAW**!")
		elif 'SmackDown' in event['name']:
			await bot.send_message(channel_sd, "@everyone, it's time for **SmackDown LIVE**!")
		elif event['ppv']:
			await bot.send_message(channel_ppv, '@everyone, **{}** has begun!'.format(event['name']))
		else:
			await debug('{} {}'.format(event['name'], event['dt']))
	await debug('showtime_schedule_task: END')

async def birthday_schedule_task():
	await bot.wait_until_ready()
	await debug('birthday_schedule_task: START')
	while not bot.is_closed:
		events = []
		dt = datetime.datetime.now()
		timer = ((24 - dt.hour - 1) * 60 * 60) + ((60 - dt.minute - 1) * 60) + (60 - dt.second)
		for s in dbhandler.superstar_birthdays():
			if not s['official_twitter']: continue
			s['dt'] = datetime.datetime(dt.year,  s['dob'].month,  s['dob'].day)
			if s['dt'] > dt:
				if events and events[0]['dt']!=s['dt']: break
				events.append(s)
				timer = (events[0]['dt'] - dt).total_seconds()
		await debug('birthday_schedule_task: sleep:{}, until:{}, event:{}'.format(timer, dt+datetime.timedelta(seconds=timer), ','.join(e['official_twitter'] for e in events)))
		await asyncio.sleep(timer)
		if events:
			tweet = twitter.tweet('Happy Birthday, {}! #WWE #BDAY\n- Sent from everyone at https://discord.gg/Q9mX5hQ #discord #fjbot'.format(', '.join(e['official_twitter'] for e in events)))
			await bot.send_message(channel_general, tweet) 
	await debug('birthday_schedule_task: END')

async def superstar_tweet_task(timer=30):
	await bot.wait_until_ready()
	await debug('superstar_tweet_task: START')
	try:
		twitter.superstar_tweet_stream(bot.loop)
		while not bot.is_closed:
			if twitter.tweets:
				for tweet in twitter.tweets:
					await bot.send_message(channel_twitter, tweet)
				twitter.tweets = []
			await asyncio.sleep(timer)
	except Exception as e:
		await debug('superstar_tweet_task: error - {}'.format(e))
	await debug('superstar_tweet_task: END')

async def chatango_log_task(timer=30):
	await bot.wait_until_ready()
	await debug('chatango_log_task: START')
	bot.loop.create_task(chatango.message_stream(bot.loop))
	await asyncio.sleep(5)
	while not bot.is_closed and chatango.bot._running:
		timer = 5 if chatango.messages else 30
		for msg in chatango.messages:
			await bot.send_message(channel_chatango, '```{}```'.format(msg))
			chatango.messages = []
		await asyncio.sleep(timer)
	await debug('chatango_log_task: END')

# bot events
@bot.event
async def on_ready():
	bot.start_dt = datetime.datetime.now()
	print('[{}] Discord: Logged in as {}({})'.format(bot.start_dt, bot.user.name, bot.user.id))
	print('------')
	await debug('FJBot: START')
	bot.loop.create_task(showtime_schedule_task())
	bot.loop.create_task(birthday_schedule_task())
	bot.loop.create_task(superstar_tweet_task())
	bot.loop.create_task(chatango_log_task())

@bot.event
async def on_member_join(member):
	role = discord.utils.get(member.server.roles, name=credentials.discord['role']['default'])
	await bot.add_roles(member, role)
	await bot.send_message(channel_general, 'Welcome to {}, {}! Say hi!'.format(member.server.name, member.mention))

@bot.event
async def on_message(message):
	if message.author.bot or not message.content.startswith('!'):
		return
	res = dbhandler.discord_command(message.content.split(' ')[0])
	if res:
		await bot.send_message(message.channel, res['response'].replace('@mention', message.author.mention))
		dbhandler.discord_command_cnt(res['id'])
	else:
		tokens = message.content.split(' ')
		message.content = '{} {}'.format(tokens[0].lower(), ' '.join(tokens[1:]))
		await bot.process_commands(message)

# mod commands
@bot.command(pass_context=True)
async def kick(ctx, member:discord.Member, reason=None):
	owner = ctx.message.server.get_member(credentials.discord['owner_id'])
	if owner==ctx.message.author:
		await bot.kick(member)
		await bot.say('{} has been kicked{}'.format(member, ' for {}.'.format(reason) if reason else '.'))
	else:
		await bot.send_message(owner, '```{}\n[#{}] {}: {}```'.format('Invalid Command', ctx.message.channel, ctx.message.author, ctx.message.content))

@bot.command(pass_context=True)
async def ban(ctx, member:discord.Member, reason=None):
	owner = ctx.message.server.get_member(credentials.discord['owner_id'])
	if owner==ctx.message.author:
		await bot.ban(member)
		await bot.say('{} has been banned{}'.format(member, ' for {}.'.format(reason) if reason else '.'))
	else:
		await bot.send_message(owner, '```{}\n[#{}] {}: {}```'.format('Invalid Command', ctx.message.channel, ctx.message.author, ctx.message.content))

@bot.command(pass_context=True)
async def clear(ctx, count=2):
	owner = ctx.message.server.get_member(credentials.discord['owner_id'])
	if owner==ctx.message.author:
		msgs = []
		async for msg in bot.logs_from(ctx.message.channel, limit=count):
			msgs.append(msg)
		await bot.delete_messages(msgs)
	else:
		await bot.send_message(owner, '```{}\n[#{}] {}: {}```'.format('Invalid Command', ctx.message.channel, ctx.message.author, ctx.message.content))

@bot.command(pass_context=True)
async def spam(ctx):
	owner = ctx.message.server.get_member(credentials.discord['owner_id'])
	if owner==ctx.message.author:
		msgs = []
		spam = []
		async for msg in bot.logs_from(ctx.message.channel, limit=100):
			c = str(msg.author) + msg.content
			if c in msgs:
				spam.append(msg)
			else:
				msgs.append(c)
		if(len(spam)>1):
			spam.append(ctx.message)
			await bot.delete_messages(spam)
		else:
			await bot.delete_message(ctx.message)
	else:
		await bot.send_message(owner, '```{}\n[#{}] {}: {}```'.format('Invalid Command', ctx.message.channel, ctx.message.author, ctx.message.content))

@bot.group(pass_context=True)
async def testt(ctx):
	if ctx.invoked_subcommand is None:
		await bot.say('Invalid testt')

@bot.command(pass_context=True)
async def playing(ctx, game=None):
	owner = ctx.message.server.get_member(credentials.discord['owner_id'])
	if owner==ctx.message.author:
		await bot.change_presence(game=discord.Game(name=game))
		await bot.say('Presence Updated.')
	else:
		await bot.send_message(owner, '```{}\n[#{}] {}: {}```'.format('Invalid Command', ctx.message.channel, ctx.message.author, ctx.message.content))

@bot.command(pass_context=True)
async def tweet(ctx, message):
	owner = ctx.message.server.get_member(credentials.discord['owner_id'])
	if owner==ctx.message.author:
		tweet_content = message + ' #fjbot'
		await bot.say('Send Tweet? [Y/N]```{}```'.format(tweet_content))
		confirm = await bot.wait_for_message(timeout=10.0, author=ctx.message.author, check=confirm_check)
		if confirm and confirm.content.upper()=='Y':
			tweet = twitter.tweet(tweet_content)
			await bot.say(tweet)
		else:
			await bot.say('Tweet cancelled.')
	else:
		await bot.send_message(owner, '```{}\n[#{}] {}: {}```'.format('Invalid Command', ctx.message.channel, ctx.message.author, ctx.message.content))

@bot.command(pass_context=True)
async def ch(ctx, message):
	owner = ctx.message.server.get_member(credentials.discord['owner_id'])
	if owner==ctx.message.author:
		if message == '!ad':
			message = discord_ad
		await bot.say('Send message to Chatango? [Y/N]```{}```'.format(message))
		confirm = await bot.wait_for_message(timeout=10.0, author=ctx.message.author, check=confirm_check)
		if confirm and confirm.content.upper()=='Y':
			ch_rooms = []
			for ch_room in credentials.chatango['rooms']:
				if chatango.bot.sendRoomMessage(ch_room, message):
					ch_rooms.append(ch_room)
			await bot.say('{}, Discord message sent to Chatango [{}].'.format(ctx.message.author.mention, ','.join(ch_rooms)))
		else:
			await bot.say('{}, Chatango message cancelled.'.format(ctx.message.author.mention))			
	else:
		await bot.send_message(owner, '```{}\n[#{}] {}: {}```'.format('Invalid Command', ctx.message.channel, ctx.message.author, ctx.message.content))

@bot.command(pass_context=True)
async def chusers(ctx):
	owner = ctx.message.server.get_member(credentials.discord['owner_id'])
	if owner==ctx.message.author:
		await bot.say('Chatango User List ({})\n {}'.format(len(chatango.users), chatango.users))			
	else:
		await bot.send_message(owner, '```{}\n[#{}] {}: {}```'.format('Invalid Command', ctx.message.channel, ctx.message.author, ctx.message.content))

@bot.command(pass_context=True)
async def ratestart(ctx, match_id):
	owner = ctx.message.server.get_member(credentials.discord['owner_id'])
	user = dbhandler.user_discord(ctx.message.author.id)
	if user['access']<2:
		await bot.send_message(owner, '```{}\n[#{}] {}: {}```'.format('Invalid Command', ctx.message.channel, ctx.message.author, ctx.message.content))	
		return
	try:
		match_id = int(match_id)
	except:
		await bot.say('Invalid `!startrating` format.\n`!startrating [match_id]`')
		return
	
	m = dbhandler.match(match_id)
	
	if m:
		await bot.say('Start Rating on [{} | {}]? [Y/N]'.format(m['match_type'], m['superstars']))
		confirm = await bot.wait_for_message(timeout=10.0, author=ctx.message.author, check=confirm_check)
		if not confirm:
			await bot.say('You took too long to confirm. Try again, {}.'.format(ctx.message.author.mention))
		else:
			confirm.content = confirm.content.upper()
			if confirm.content=='Y':
				global current_match
				current_match = m
				chatango.current_match = m
				msg = 'Match Rating has begun! Use command `!rate [number]` to give the match a 1-5 star rating. [{} | {}]'.format(m['match_type'], m['superstars'])
				await bot.say(msg)
				for ch_room in credentials.chatango['rooms']:
					chatango.bot.sendRoomMessage(ch_room, msg)
			else:
				await bot.say('RateStart cancelled.')
	else:
		await bot.say('Match not found.')

@bot.command(pass_context=True)
async def rateend(ctx):
	user = dbhandler.user_discord(ctx.message.author.id)
	if user['access']<2:
		await bot.send_message(owner, '```{}\n[#{}] {}: {}```'.format('Invalid Command', ctx.message.channel, ctx.message.author, ctx.message.content))	
		return
	global current_match
	if current_match:
		match_id = current_match['id']
		current_match = {}
		chatango.current_match = {}
		m = dbhandler.match(match_id)
		msg = 'Match Rating has ended. Received a total of {} ({:.3f}). [{} | {}]'.format(''.join(['★' if m['rating']>=i else '☆' for i in range(1,6)]), m['rating'], m['match_type'], m['superstars'])
		await bot.say(msg)
		for ch_room in credentials.chatango['rooms']:
			chatango.bot.sendRoomMessage(ch_room, msg)
	else:
		await bot.say('No current match set.')

# public commands
@bot.command(pass_context=True)
async def report(ctx):
	owner = ctx.message.server.get_member(credentials.discord['owner_id'])
	if owner:
		await bot.send_message(owner, '```\nREPORT\n[#{}] {}: {}```'.format(ctx.message.channel, ctx.message.author, ctx.message.content))
		await bot.say('Report sent.')

@bot.command()
async def commands():
	mcs = dbhandler.misc_commands()
	await bot.say('```Miscellaneous Commands:\n{}```'.format('\n'.join(mcs)))

@bot.command()
async def uptime():
	await bot.say('```Uptime: {}```'.format(datetime.datetime.now()-bot.start_dt))

@bot.command()
async def countdown():
	n = 5
	while n > 0:
		await bot.say('**`{}`**'.format(n))
		await asyncio.sleep(1)
		n = n -1
	await bot.say('**`GO!`**')

@bot.command()
async def flip():
	await bot.say('You flipped `{}`.'.format('Heads' if random.getrandbits(1) else 'Tails'))

@bot.command()
async def roll():
	await bot.say('You rolled a `{}` and a `{}`.'.format(random.randint(1,6), random.randint(1,6)))

@bot.command(pass_context=True)
async def slap(ctx, member:discord.Member, reason=None):
	if member.bot:
		await bot.say("*{} slapped {}'s cheeks for trying to abuse a bot*".format(member.mention, ctx.message.author.mention))
	elif member == ctx.message.author:
		await bot.say('{}, you god damn masochist.'.format(member.mention))		
	else:
		await bot.say('*{} slapped {}{}*'.format(ctx.message.author.mention, member.mention, ' for {}'.format(reason) if reason else ''))

@bot.command(pass_context=True)
async def tickle(ctx, member:discord.Member, reason=None):
	if(member.bot):
		await bot.say("*{} spread {}'s cheeks and tickled the inside for trying to touch bot*".format(member.mention, ctx.message.author.mention))
	elif member == ctx.message.author:
		await bot.say('{}, tickling yourself are you now? Pathetic..'.format(member.mention))		
	else:
		await bot.say('*{} tickled {}{}*'.format(ctx.message.author.mention, member.mention, ' for {}'.format(reason) if reason else ''))

@bot.command(pass_context=True)
async def mock(ctx, member:discord.Member):
	if member.bot: 
		await bot.say('No.')
		return
	async for msg in bot.logs_from(ctx.message.channel, limit=50):
		if msg.content.startswith('!') or '@' in msg.content: continue;
		if msg.author == member:
			mock_msg = ''.join([l.upper() if random.getrandbits(1) else l.lower() for l in msg.content])
			await bot.say('```"{}"\n    - {}```'.format(mock_msg, member))
			break

@bot.command()
async def invite():
	await bot.say(discord_ad)

@bot.command(pass_context=True)
async def role(ctx):
	await bot.say('Your Roles: {}'.format([role.name for role in ctx.message.author.roles]).replace('@',''))

@bot.command(pass_context=True)
async def id(ctx):
	await bot.send_message(ctx.message.author, 'Your discord_id is: `{}`\nLink it to your http://wwe.fancyjesse.com profile.'.format(ctx.message.author.id))
	await bot.say('{}, your ID has been DMed. Please visit http://wwe.fancyjesse.com to link your account.'.format(ctx.message.author.mention))

@bot.command(pass_context=True)
async def verify(ctx):
	user = dbhandler.user_discord(ctx.message.author.id)
	if user:
		await bot.say('Your Discord is successfully linked to `{}` on http://wwe.fancyjesse.com'.format(user['username']))
	else:
		await bot.say('You are not registered.\nPlease visit http://wwe.fancyjesse.com to register.\nThen link your Discord account by using command `!id`.')

@bot.command(pass_context=True)
async def tweets(ctx, *args):
	try:
		superstar = args[0]
		count = int(args[1]) if len(args)>1 else 1
		count = 1 if count<1 else count
		count = 5 if count>5 else count
	except:		
		await bot.say('Invalid `!tweets` format.\n`!tweets [superstar] [count]`')
		return
	if superstar.startswith('@'):
		id = superstar
	elif superstar.lower() == 'wwe':
		id = '@WWE'
	else:
		bio = dbhandler.superstar_bio('%'+superstar.replace(' ','%')+'%')
		id = bio['official_twitter_id'] if bio else False	
	if id:
		tweets = twitter.superstar_tweets(id, count)
		for tweet in tweets:
			await bot.say('https://twitter.com/statuses/{}'.format(tweet.id))
	else:
		await bot.say("Unable to find Tweets for '{}'".format(superstar))

# WWE-Matches
@bot.command()
async def ppv():
	ppvs = dbhandler.ppvs()
	await bot.say('```Upcoming PPVs\n-------------\n{}```'.format('\n'.join(['{} - {}'.format(e['date'],e['name']) for e in ppvs])))

@bot.command()
async def bio(superstar):
	bio = dbhandler.superstar_bio('%'+superstar.replace(' ','%')+'%')
	if bio:
		name = bio['name'] + (' ({})'.format(bio['official_twitter']) if bio['official_twitter'] else '')
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
	else: 
		msg = "Unable to find Superstar matching '{}'".format(superstar)
	await bot.say(msg)

@bot.command()
async def birthdays():
	bdays = dbhandler.superstar_birthdays()
	await bot.say('```Birthdays This Month\n-------------\n{}```'.format('\n'.join(['[{}] {}'.format(b['dob'],b['name']) for b in bdays])))

@bot.command()
async def superstars():
	sl = dbhandler.superstars()
	sl = [s['name'] for s in sl]
	await bot.say('```{}```'.format('\n'.join(sl)))

@bot.command()
async def leaderboard():
	lb = dbhandler.leaderboard()
	lb = ['{}. {} ({:,})'.format(i+1,l['username'],l['total_points']) for i, l in enumerate(lb)]
	await bot.say('```TOP 10 (Season 2)\n------\n{}```'.format('\n'.join(lb)))

@bot.command()
async def leaderboard_s1():
	lb = dbhandler.leaderboard_s1()
	lb = ['{}. {} ({:,})'.format(i+1,l['username'],l['points']) for i, l in enumerate(lb)]
	await bot.say('```TOP 10 (Season 1)\n------\n{}```'.format('\n'.join(lb)))

@bot.command()
async def titles():
	ts = dbhandler.titles()
	ts = ['{}\n{}'.format(t['title'], t['superstar']) for t in ts]
	await bot.say('```WWE Titles\n----------\n{}```'.format('\n\n'.join(ts)))

@bot.command()
async def rumble():
	await bot.say('Join the Rumble at: https://fancyjesse.com/projects/wwe/royalrumble')

@bot.command(pass_context=True)
async def page(ctx):
	user = dbhandler.user_discord(ctx.message.author.id)
	if user:
		await bot.say("{}'s WWE Matches Page\nhttps://fancyjesse.com/projects/wwe/user?user_id={}".format(ctx.message.author.mention, user['id']))
	else:
		await bot.say('You are not registered.\nPlease visit http://wwe.fancyjesse.com to register.\nThen link your Discord account by using command `!id`.')

@bot.command(pass_context=True)
async def stats(ctx):
	user = dbhandler.user_discord(ctx.message.author.id)
	if user:
		user = dbhandler.user_stats(user['id'])
		try:
			ratio = '{:.3f}'.format(user['wins']/user['losses'])
		except:
			ratio = 'N/A'
		await bot.say('```Username: {}\nWins: {}\nLosses: {}\nRatio: {}```'.format(user['username'], user['wins'], user['losses'], ratio))
	else:
		await bot.say('You are not registered.\nPlease visit http://wwe.fancyjesse.com to register.\nThen link your Discord account by using command `!id`.')

@bot.command(pass_context=True)
async def stats_s1(ctx):
	user = dbhandler.user_discord(ctx.message.author.id)
	if user:
		user = dbhandler.user_stats_s1(user['id'])
		try:
			ratio = '{:.3f}'.format(user['s1_wins']/user['s1_losses'])
		except:
			ratio = 'N/A'
		await bot.say('```Username: {}\nPoints: {:,}\nWins: {}\nLosses: {}\nRatio: {}```'.format(user['username'], user['s1_points'], user['s1_wins'], user['s1_losses'], ratio))
	else:
		await bot.say('You are not registered.\nPlease visit http://wwe.fancyjesse.com to register.\nThen link your Discord account by using command `!id`.')

@bot.command(pass_context=True)
async def points(ctx):
	user = dbhandler.user_discord(ctx.message.author.id)
	if user:
		user = dbhandler.user_stats(user['id'])
		await bot.say('```Username: {}\nTotal Points: {:,}\nAvailable Points: {:,}```'.format(user['username'], user['total_points'], user['available_points']))
	else:
		await bot.say('You are not registered.\nPlease visit http://wwe.fancyjesse.com to register.\nThen link your Discord account by using command `!id`.')

@bot.command(pass_context=True)
async def bets(ctx):
	user = dbhandler.user_discord(ctx.message.author.id)
	if user:
		bets = dbhandler.user_bets(user['id'])
		if bets:
			await bot.say("{}'s Current Bets\n```{}```".format(ctx.message.author.mention, '\n'.join(['Match {}\n  {:,} points on {}\n  Potential Pot Winnings: {}%'.format(bet['match_id'],bet['points'],bet['contestants'],bet['pot_cut']*100) for bet in bets])))
		else:
			await bot.say('{} has no bets placed on Matches.'.format(ctx.message.author.mention))
	else:
		await bot.say('You are not registered.\nPlease visit http://wwe.fancyjesse.com to register.\nThen link your Discord account by using command `!id`.')

@bot.command()
async def match(match_id):
	try:
		match_id = int(match_id)
	except:
		await bot.say('Invalid `!match` format.\n`!match [match_id]`')
		return
	m = dbhandler.match(match_id)
	if m:
		msg = '[Match {}] {}\nEvent: {}\nRating: {} ({:.3f})\nPot: {:,} ({}x) -> {}\nBets: {}\n{}{} {}\n\t{}\nTeam Won: {}{}'.format(
			m['id'],
			m['date'],
			m['event'],
			''.join(['★' if m['rating']>=i else '☆' for i in range(1,6)]),
			m['rating'],
			m['base_pot'],
			m['bet_multiplier'] if m['team_won'] else '?',
			'{:,}'.format(m['total_pot']) if m['team_won'] else 'TBD',
			'Open' if m['bet_open'] else 'Closed',
			m['title']+'\n' if m['title'] else '',
			m['match_type'],
			' ('+m['match_note']+')' if m['match_note'] else '',
			'\n\t'.join(['Team {}. ({}x) {}'.format(t[0],t[1],t[2]) for t in m['team']]),
			m['team_won'] if m['team_won'] else 'N/A',
			' ('+m['winner_note']+')' if m['winner_note'] else '')
		await bot.say('```{}```'.format(msg))
	else:
		await bot.say('Match {} not found.'.format(match_id))

@bot.command()
async def matches():
	match_set = dbhandler.open_matches()
	if match_set:
		matches = ['[Match {}] {}\nEvent: {}\nBase Pot: {:,}\nBets: {}\n{}{}{}\n\t{}'.format(
			v['id'],
			v['date'],
			v['event'],
			v['base_pot'],
			'Open' if v['bet_open'] else 'Closed',
			v['title']+'\n' if v['title'] else '',
			v['match_type'],
			' ('+v['match_note']+')' if v['match_note'] else '',
			'\n\t'.join(['Team {}. ({}x) {}'.format(t[0],t[1],t[2]) for t in v['team']]
		)) for k,v in match_set.items()]
		msg = 'Open Matches\n------------'
		for m in matches:
			if len(msg+m) > 2000:
				await bot.say('```{}```'.format(msg))
				msg = '...\n\n'
			else:
				msg = msg + '\n\n'
			msg = msg + m
		await bot.say('```{}```'.format(msg))
	else:
		await bot.say('No open bet matches available.')

@bot.command(pass_context=True)
async def bet(ctx, *args):
	user = dbhandler.user_discord(ctx.message.author.id)
	if user:
		try:
			bet = int(args[0])
			match_id = int(args[1])
			team = int(args[2])
		except:		
			await bot.say('Invalid `!bet` format.\n`!bet [bet_amount] [match_id] [team]`')
			return
		if bet<1:
			await bot.say('Invalid bet. Try again, {}.'.format(ctx.message.author.mention))
			return
		user = dbhandler.user_stats(user['id'])
		if user['available_points'] < bet:
			await bot.say('Insufficient points available. Try again, {}.'.format(ctx.message.author.mention))
			return
		match = dbhandler.open_matches()
		if not match:
			await bot.say('Match not found. Try again, {}.\nEnter `!matches` to view current matches.'.format(ctx.message.author.mention))
			return
		match = match.get(match_id, None)
		if not match:
			await bot.say('Match not found. Try again, {}.\nEnter `!matches` to view current matches.'.format(ctx.message.author.mention))
			return
		if not match['bet_open']:
			await bot.say('Match bets are closed. Try again, {}.\nEnter `!matches` to view current matches.'.format(ctx.message.author.mention))
			return
		tm = {}
		for t in match['team']:
			if team==t[0]:
				tm = t[2]
				break
		if not tm:
			await bot.say('Invalid Team. Try again, {}.'.format(ctx.message.author.mention))
			return
		ub = dbhandler.user_bet_check(user['id'], match['id'])
		if ub:
			for t in match['team']:
				if ub['team']==t[0]:
					tm = t[2]
					break
			await bot.say('{}, you already have a {:,} bet placed on {}.'.format(ctx.message.author.mention, ub['points'], tm))
			return
		await bot.say('{}, are you sure you want to bet **{:,} points** on **{}**? [Y/N]'.format(ctx.message.author.mention, bet, tm))
		confirm = await bot.wait_for_message(timeout=10.0, author=ctx.message.author, check=confirm_check)
		if not confirm:
			await bot.say('You took too long to confirm. Try again, {}.'.format(ctx.message.author.mention))
		else:
			confirm.content = confirm.content.upper()
			if confirm.content=='Y':
				if dbhandler.user_bet(user['id'], match['id'], team, bet):
					pot = dbhandler.match(match['id'])['base_pot']
					await bot.say('{} placed a {:,} point bet on Match {} for **{}**!\nMatch Base Pot is now **{:,}** points.'.format(ctx.message.author.mention, bet, match['id'], tm, pot))
				else:
					await bot.say('{}, unable to process bet.'.format(ctx.message.author.mention))
			elif confirm.content=='N':
				await bot.say("{}'s bet cancelled. Coward.".format(ctx.message.author.mention))
	else:
		await bot.say('You are not registered.\nPlease visit http://wwe.fancyjesse.com to register.\nThen link your Discord account by using command `!id`.')

@bot.command(pass_context=True)
async def rate(ctx, *args):
	user = dbhandler.user_discord(ctx.message.author.id)
	if user:
		try:
			if current_match:
				match_id = current_match['id']
				rate = float(args[0])
			else:
				match_id = int(args[0])
				rate = float(args[1])
		except:		
			await bot.say('Invalid `!rate` format.\n`!rate [match_id] [rating]`')
			return
		if rate<0 or rate>5:
			await bot.say('Invalid match rating. Try again, {}.'.format(ctx.message.author.mention))
			return
		match = dbhandler.match(match_id)
		if match:
			#if match['team_won']==0:
			#	await bot.say('Match rating unavailable - No decision yet, {}.'.format(ctx.message.author.mention))
			if (datetime.datetime.today().date() - match['date']).days > 2:
				await bot.say('Match rating unavailable - Past 48 hours of event date, {}.'.format(ctx.message.author.mention))
			else:
				if not dbhandler.user_rate(user['id'], match['id'], rate):
					await bot.say('Something went wrong. Try again later, {}.'.format(ctx.message.author.mention))
					return
				if rate:
					stars = ''
					for i in range(1,6):
						if rate>=i:
							stars += '★'
						else:
							stars += '☆'
					await bot.say('{} gave `Match {}` {} ({})'.format(ctx.message.author.mention, match['id'], stars, rate))
				else:
					await bot.say('{} removed their rating for `Match {}`.'.format(ctx.message.author.mention, match['id']))
		else:
			await bot.say('Match {} not found.'.format(match_id))
	else:
		await bot.say('You are not registered.\nPlease visit http://wwe.fancyjesse.com to register.\nThen link your Discord account by using command `!id`.')

# testing
@bot.command(pass_context=True)
async def bet2(ctx, *args):
	user = dbhandler.user_discord(ctx.message.author.id)
	if user:
		try:
			bet = int(args[0])
			match_id = int(args[1])
			team = int(args[2])
		except:		
			await bot.say('Invalid `!bet2` format.\n`!bet [bet_amount] [match_id] [team]`')
			return
		if bet<1:
			await bot.say('Invalid bet. Try again, {}.'.format(ctx.message.author.mention))
			return
		user = dbhandler.user_stats2(user['id'])
		if user['available_points'] < bet:
			await bot.say('Insufficient points available. Try again, {}.'.format(ctx.message.author.mention))
			return
		match = dbhandler.open_matches()
		if not match:
			await bot.say('Match not found. Try again, {}.\nEnter `!matches` to view current matches.'.format(ctx.message.author.mention))
			return
		match = match.get(match_id, None)
		if not match:
			await bot.say('Match not found. Try again, {}.\nEnter `!matches` to view current matches.'.format(ctx.message.author.mention))
			return
		if not match['bet_open']:
			await bot.say('Match bets are closed. Try again, {}.\nEnter `!matches` to view current matches.'.format(ctx.message.author.mention))
			return
		tm = {}
		for t in match['team']:
			if team==t[0]:
				tm = t[2]
				break
		if not tm:
			await bot.say('Invalid Team. Try again, {}.'.format(ctx.message.author.mention))
			return
		ub = dbhandler.user_bet_check2(user['id'], match['id'])
		if ub:
			for t in match['team']:
				if ub['team']==t[0]:
					tm = t[2]
					break
			await bot.say('{}, you already have a {:,} bet placed on {}.'.format(ctx.message.author.mention, ub['points'], tm))
			return
		await bot.say('{}, are you sure you want to bet **{:,} points** on **{}**? [Y/N]'.format(ctx.message.author.mention, bet, tm))
		confirm = await bot.wait_for_message(timeout=10.0, author=ctx.message.author, check=confirm_check)
		if not confirm:
			await bot.say('You took too long to confirm. Try again, {}.'.format(ctx.message.author.mention))
		else:
			confirm.content = confirm.content.upper()
			if confirm.content=='Y':
				if dbhandler.user_bet2(user['id'], match['id'], team, bet):
					pot = dbhandler.match(match['id'])['base_pot']
					await bot.say('{} placed a {:,} point bet on Match {} for **{}**!\nMatch Base Pot is now **{:,}** points.'.format(ctx.message.author.mention, bet, match['id'], tm, pot))
				else:
					await bot.say('{}, unable to process bet.'.format(ctx.message.author.mention))
			elif confirm.content=='N':
				await bot.say("{}'s bet cancelled. Coward.".format(ctx.message.author.mention))
	else:
		await bot.say('You are not registered.\nPlease visit http://wwe.fancyjesse.com to register.\nThen link your Discord account by using command `!id`.')

@bot.command()
async def leaderboard1():
	lb = dbhandler.leaderboard()
	lb = ['{}. {} ({:,})'.format(i+1,l['username'],l['total_points']) for i, l in enumerate(lb)]
	await bot.say('```TOP 10 ( (user_bet/winner_pot)*(total_pot*bet_multi) )\n------\n{}```'.format('\n'.join(lb)))

@bot.command()
async def leaderboard2():
	lb = dbhandler.leaderboard2()
	lb = ['{}. {} ({:,})'.format(i+1,l['username'],l['total_points']) for i, l in enumerate(lb)]
	await bot.say('```TOP 10 ( (loser_bet_cnt/winner_bet_cnt)*(user_bet*bet_multi) )\n------\n{}```'.format('\n'.join(lb)))

if __name__ == '__main__':
	try:
		bot.run(credentials.discord['access_token'])
	except KeyboardInterrupt:
		pass
	finally:
		bot.logout()
		print('[{}] FJBOT: END'.format(datetime.datetime.now()))
		print('Total Tasks: {}'.format(len(asyncio.Task.all_tasks())))
		print('Active Tasks: {}'.format(len([t for t in asyncio.Task.all_tasks() if not t.done()])))
