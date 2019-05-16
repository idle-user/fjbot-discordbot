import asyncio
import datetime
import json

from discord.ext import commands
import discord
import tweepy

from utils.fjclasses import DiscordUser
from utils import checks, quickembed
import config


class Twitter(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.auth = tweepy.OAuthHandler(config.twitter['consumer_key'], config.twitter['consumer_secret'])
		self.auth.set_access_token(config.twitter['access_token'], config.twitter['access_token_secret'])
		self.twitter = tweepy.API(self.auth)
		self.bot.log('[{}] Twitter {}: START'.format(datetime.datetime.now(), self.twitter.me().screen_name))
		self.bot.loop.create_task(self.superstar_birthday_task())
		#self.start_log_stream()
		#self.start_dm_stream()
		#self.dm_test()

	def __unload(self):
		if self.logstream:
			self.logstream.running = False
		if self.dmstream:
			self.dmstream.running = False

	class LogStreamListener(tweepy.StreamListener):
		def __init__(self, myapi, ids):
			self.myapi = myapi
			self.ids = ids
			super(Twitter.LogStreamListener, self).__init__()
		def on_error(self, status_code):
			# self.bot.log('Twitter.SuperstarListener.on_error: {}'.format(status_code))
			if status_code == 420:
				return False
		def on_data(self, raw_data):
			data = json.loads(raw_data)
			if 'message_create' in data or '105715916' in data:
				print('data: {}'.format(data['user']['screen_name']))
				return False
		def on_status(self, status):
			print('TWEET: {}: {}'.format(status.user.screen_name, status.text))
			return
			if not (status.retweeted or 'RT @' in status.text) and status.user.id_str in self.ids:
				# tweet user_id in list and not a retweet
				if not status.in_reply_to_user_id or self.myapi.twitter.get_user(status.in_reply_to_user_id_str).verified:
					# tweet must be non-reply or reply to verified account
					tweet = 'https://twitter.com/statuses/{}'.format(status.id)
					self.myapi.bot.loop.create_task(self.myapi.tweet_log(tweet))
		def on_direct_message(self, status):
			print('on_dm')
			#self.myapi.twitter.send_direct_message(screen_name=status.author.screen_name, text='test')

	class DMStreamListener(tweepy.StreamListener):
		def __init__(self, myapi):
			self.myapi = myapi
			super(Twitter.DMStreamListener, self).__init__()
		def on_error(self, status_code):
			print(status_code)
			if status_code == 420:
				return False
		def on_data(self, status):
			print('data:',status)
		def on_direct_message(self, status):
			print('DM')
			#user = self.api.get_user(self.destname)
			#self.myapi.live_dm(user.id, 'test')

	def start_log_stream(self):
		log_superstars = [s for s in self.bot.dbhandler.superstar_twitter() if s['twitter_discord_log']]
		self.bot.log('Twitter Logging: [{}]'.format(', '.join([s['twitter_username'] for s in log_superstars])))
		log_ids = [s['twitter_id'] for s in log_superstars]
		log_ids.append('7517222') # @WWE
		log_ids.append('1357803824') # @totaldivaseps
		log_ids.append('105715916') # @fancyjesse
		log_ids = list(filter(None, log_ids))
		self.bot.log('Starting Twitter Log Stream ...')
		self.logstream = tweepy.Stream(self.auth, self.LogStreamListener(self, log_ids))
		self.logstream.filter(follow=log_ids, is_async=True)

	def start_dm_stream(self):
		self.bot.log('Starting Twitter DM Stream ...')
		self.dmstream = tweepy.Stream(self.auth, self.DMStreamListener(self))
		#self.dmstream.filter(follow=['105715916',], async=True)
		# self.dmstream.userstream(async=True) #depricated - use home_timeline, user_timeline

	def dm_test(self):
		next_cursor = self.twitter.direct_messages(count=1)[0].next_cursor
		while next_cursor is not None:
			if next_cursor is not None:
				direct_messages = self.twitter.direct_messages(cursor=next_cursor, count=50)
			else:
				direct_messages = connection.direct_messages(count=50)
			try:
				next_cursor = direct_messages[0].next_cursor
			except:
				next_cursor = None
			print(len(direct_messages))
			for dm in direct_messages:
				for event in dm.events:
					print(event.id)
		print('End dm_test')

	def latest_tweets(self, twitter_id, count=1):
		return self.twitter.user_timeline(id=twitter_id, count=count, include_rts=False)

	def live_tweet(self, msg):
		status = self.twitter.update_status(msg)
		link = 'https://twitter.com/statuses/{}'.format(status.id)
		return link

	def live_dm(self, recipient_id, message):
		self.twitter.send_direct_message(type='message_create', text=message, recipient_id=recipient_id)

	""" 
	def live_dm2(self, recipient_id, msg):
		event = {
			'event': {
				'type': 'message_create',
				'message_create': {
						'target': {
						'recipient_id': recipient_id
					},
					'message_data': {
						'text': msg
					}
				}
			}
		}
		self.twitter.send_direct_message_new(event)
	"""

	async def tweet_log(self, message):
		channel = self.bot.get_channel(config.discord['channel']['twitter'])
		await channel.send(message)

	async def superstar_birthday_task(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed():
			events = []
			dt = datetime.datetime.now()
			timer = ((24 - dt.hour - 1) * 60 * 60) + ((60 - dt.minute - 1) * 60) + (60 - dt.second)
			for s in self.bot.dbhandler.superstar_birthdays():
				if not s['twitter_name']: continue
				s['dt'] = datetime.datetime(dt.year,  s['dob'].month,  s['dob'].day)
				if s['dt'] > dt:
					if events and events[0]['dt']!=s['dt']: break
					events.append(s)
					timer = (events[0]['dt'] - dt).total_seconds()
			self.bot.log('birthday_schedule_task: sleep_until:{}, event:{}'.format(dt+datetime.timedelta(seconds=timer), ','.join(e['twitter_name'] for e in events)))
			await asyncio.sleep(timer)
			if events:
				tweet_link = self.live_tweet('Happy Birthday, {}! #BDAY\n- Sent from everyone at https://discord.gg/Q9mX5hQ #discord #fjbot'.format(', '.join(e['twitter_name'] for e in events)))
				channel = self.bot.get_channel(config.discord['channel']['twitter'])
				await channel.send(tweet_link)
		self.bot.log('END birthday_schedule_task')
		
	@commands.command(name='tweetdm')
	@checks.is_owner()
	async def send_tdm(self, ctx, *, msg):
		id = '105715916'
		self.live_dm(recipient_id=id, message=msg)
		
	@commands.command(name='tweetsend')
	@checks.is_owner()
	async def send_tweet(self, ctx, *, message:str):
		await ctx.send('Send Tweet? [Y/N]```{}```'.format(message))
		confirm = await self.bot.wait_for('message', check=checks.confirm, timeout=10.0)
		if confirm and confirm.content.upper()=='Y':
			tweet_link = self.live_tweet(message)
			channel = self.bot.get_channel(config.discord['channel']['twitter'])
			await channel.send(tweet_link)
		else:
			await ctx.send('`Tweet cancelled.`')

	@commands.command(name='viewtweets', aliases=['tweets'])
	async def superstar_tweets(self, ctx, name, limit=1):
		try:
			superstar = name
			limit = 1 if limit<1 else limit
			limit = 5 if limit>5 else limit
		except:
			await ctx.send('Invalid `!tweets` format.\n`!tweets [superstar] [limit]`')
			return
		bio = self.bot.dbhandler.superstar_by_name('%'+superstar.replace(' ','%')+'%')
		id = bio['twitter_id'] if bio else '@{}'.format(superstar)
		if id:
			tweets = self.latest_tweets(id, limit)
			for tweet in tweets:
				await ctx.send('https://twitter.com/statuses/{}'.format(tweet.id))
		else:
			await ctx.send("Unable to find Tweets for `{}`'".format(superstar))

	@commands.command(name='tlist')
	async def superstar_stream_list(self):
		log_superstars = [s for s in self.bot.dbhandler.superstar_twitter() if s['twitter_discord_log']]
		await ctx.send('```Currently Streaming: [{}]```'.format(', '.join([s['name'] for s in log_superstars])))

	@commands.command(name='tadd', hidden=True)
	@checks.is_mod()
	async def add_superstar_stream(self, ctx, *, name):
		superstar = self.bot.dbhandler.superstar_by+name('%'+name.replace(' ','%')+'%')
		if not superstar:
			await ctx.send('Unable to find Superstar matching `{}`'.format(name))
			return
		if superstar['twitter_id']:
			self.bot.dbhandler.superstar_update_twitter_log(superstar['id'], 1)
			await ctx.send('`Followed {}`'.format(superstar['twitter_name']))
		else:
			await ctx.send('Unable to find Twitter account for `{}`'.format(superstar['name']))

	@commands.command(name='tremove', hidden=True)
	@checks.is_mod()
	async def remove_superstar_stream(self, ctx, *, name):
		superstar = self.bot.dbhandler.superstar_by_name('%'+name.replace(' ','%')+'%')
		if not superstar:
			await ctx.send('Unable to find Superstar matching `{}`'.format(name))
			return
		if superstar['twitter_id']:
			self.bot.dbhandler.superstar_update_twitter_log(superstar['id'], 0)
			await ctx.send('`Unfollowed {}`'.format(superstar['twitter_name']))
		else:
			await ctx.send('Unable to find Twitter account for `{}`'.format(superstar['name']))

	@commands.command(name='tupdate', hidden=True)
	@checks.is_admin()
	async def update_twitter_ids(self):
		self.bot.log('Updating Superstar Twitter IDs')
		for s in self.bot.dbhandler.superstar_twitter():
			try:
				twitter_user = self.twitter.get_user(s['twitter_username'])
				twitter_id = twitter_user.id_str if twitter_user.verified else ''
				self.bot.dbhandler.superstar_update_twitter_id(s['id'], twitter_id)
				self.bot.log('Updated {}: {} ({})'.format(s['name'], s['twitter_name'], twitter_id))
			except:
				self.bot.log('Error {}: {}'.format(s['name'], s['twitter_name']))
			await asyncio.sleep(0.5)

def setup(bot):
	bot.add_cog(Twitter(bot))
