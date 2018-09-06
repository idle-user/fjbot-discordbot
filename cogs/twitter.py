import asyncio
import datetime

from discord.ext import commands
import discord
import tweepy

from utils import checks, credentials


class Twitter:

	def __init__(self, bot):
		self.bot = bot
		self.channel_general = discord.Object(id=credentials.discord['channel']['general'])
		self.channel_twitter = discord.Object(id=credentials.discord['channel']['twitter'])
		self.auth = tweepy.OAuthHandler(credentials.twitter['consumer_key'], credentials.twitter['consumer_secret'])
		self.auth.set_access_token(credentials.twitter['access_token'], credentials.twitter['access_token_secret'])
		self.twitter = tweepy.API(self.auth)
		self.bot.log('[{}] Twitter {}: START'.format(datetime.datetime.now(), self.twitter.me().screen_name))
		self.bot.loop.create_task(self.superstar_birthday_task())
		self.start_stream()

	def __unload(self):
		self.stream.running = False

	class StreamListener(tweepy.StreamListener):
		def __init__(self, myapi, ids):
			self.myapi = myapi
			self.ids = ids
			super(Twitter.StreamListener, self).__init__()
		def on_error(self, status_code):
			# self.bot.log('Twitter.SuperstarListener.on_error: {}'.format(status_code))
			if status_code == 420:
				return False
		def on_status(self, status):
			# print('TWEET: {}: {}'.format(status.user.screen_name, status.text))
			if not (status.retweeted or 'RT @' in status.text) and status.user.id_str in self.ids:
				# tweet user_id in list and not a retweet
				if not status.in_reply_to_user_id or self.myapi.twitter.get_user(status.in_reply_to_user_id_str).verified:
					# tweet must be non-reply or reply to verified account
					tweet = 'https://twitter.com/statuses/{}'.format(status.id)
					self.myapi.bot.loop.create_task(self.myapi.tweet_log(tweet))
		def on_direct_message(self, status):
			self.myapi.send_direct_message(screen_name=status.author.screen_name, text='test')

	def start_stream(self):
		log_superstars = [s for s in self.bot.dbhandler.superstar_twitter() if s['twitter_discord_log']]
		self.bot.log('Twitter Logging: [{}]'.format(', '.join([s['name'] for s in log_superstars])))
		log_ids = [s['twitter_id'] for s in log_superstars]
		log_ids.append('7517222') # @WWE
		log_ids.append('1357803824') # @totaldivaseps
		log_ids = list(filter(None, log_ids))
		self.bot.log('Starting Twitter Stream ...')
		self.stream = tweepy.Stream(self.auth, self.StreamListener(self, log_ids))
		self.stream.filter(follow=log_ids, async=True)

	def latest_tweets(self, twitter_id, count=1):
		return self.twitter.user_timeline(id=twitter_id, count=count, include_rts=False)

	def live_tweet(self, msg):
		status = self.twitter.update_status(msg)
		link = 'https://twitter.com/statuses/{}'.format(status.id)
		return link

	async def tweet_log(self, message):
		await self.bot.send_message(self.channel_twitter, message)

	async def superstar_birthday_task(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed:
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
				await self.bot.send_message(self.channel_general, tweet_link) 
		self.bot.log('END birthday_schedule_task')
		
	@commands.command(name='sendtweet', pass_context=True)
	@checks.is_owner()
	async def send_tweet(self, ctx, *, message:str):
		await self.bot.say('Send Tweet? [Y/N]```{}```'.format(message))
		confirm = await self.bot.wait_for_message(timeout=10.0, author=ctx.message.author, check=checks.confirm)
		if confirm and confirm.content.upper()=='Y':
			tweet_link = self.live_tweet(message)
			await self.bot.say(tweet_link)
		else:
			await self.bot.say('`Tweet cancelled.`')
	
	@commands.command(name='viewtweets', aliases=['tweets'], pass_context=True)
	async def superstar_tweets(self, ctx, *args):
		try:
			superstar = args[0]
			count = int(args[1]) if len(args)>1 else 1
			count = 1 if count<1 else count
			count = 5 if count>5 else count
		except:		
			await self.bot.say('Invalid `!tweets` format.\n`!tweets [superstar] [count]`')
			return
		bio = self.bot.dbhandler.superstar_bio('%'+superstar.replace(' ','%')+'%')
		id = bio['twitter_id'] if bio else '@{}'.format(superstar)	
		if id:
			tweets = self.latest_tweets(id, count)
			for tweet in tweets:
				await self.bot.say('https://twitter.com/statuses/{}'.format(tweet.id))
		else:
			await self.bot.say("Unable to find Tweets for `{}`'".format(superstar))

	@commands.command(name='tlist')
	async def superstar_stream_list(self):
		log_superstars = [s for s in self.bot.dbhandler.superstar_twitter() if s['twitter_discord_log']]
		await self.bot.say('```Currently Streaming: [{}]```'.format(', '.join([s['name'] for s in log_superstars])))

	@commands.command(name='tadd', pass_context=True, hidden=True)
	@checks.is_mod()
	async def add_superstar_stream(self, ctx, superstar_name):
		superstar = self.bot.dbhandler.superstar_bio('%'+superstar_name.replace(' ','%')+'%')
		if not superstar:
			await self.bot.say('Unable to find Superstar matching `{}`'.format(superstar_name))
			return
		if superstar['twitter_id']:
			self.bot.dbhandler.superstar_update_twitter_log(superstar['id'], 1)
			await self.bot.say('`Followed {}`'.format(superstar['twitter_name']))
		else:
			await self.bot.say('Unable to find Twitter account for `{}`'.format(superstar['name']))

	@commands.command(name='tremove', pass_context=True, hidden=True)
	@checks.is_mod()
	async def remove_superstar_stream(self, ctx, superstar_name):
		superstar = self.bot.dbhandler.superstar_bio('%'+superstar_name.replace(' ','%')+'%')
		if not superstar:
			await self.bot.say('Unable to find Superstar matching `{}`'.format(superstar_name))
			return
		if superstar['twitter_id']:
			self.bot.dbhandler.superstar_update_twitter_log(superstar['id'], 0)
			await self.bot.say('`Unfollowed {}`'.format(superstar['twitter_name']))
		else:
			await self.bot.say('Unable to find Twitter account for `{}`'.format(superstar['name']))

	@commands.command(name='tupdate', pass_context=True, hidden=True)
	@checks.is_owner()
	async def update_twitter_ids(self):
		self.bot.log('Updating Superstar Twitter IDs')
		for s in self.bot.dbhandler.superstar_twitter():
			try:
				twitter_user = self.twitter.get_user(s['twitter_name'])
				twitter_id = twitter_user.id_str if twitter_user.verified else ''
				self.bot.dbhandler.superstar_update_twitter_id(s['id'], twitter_id)
				self.bot.log('Updated {}: {} ({})'.format(s['name'], s['twitter_name'], twitter_id))
			except:
				self.bot.log('Error {}: {}'.format(s['name'], s['twitter_name']))
			await asyncio.sleep(0.5)


def setup(bot):
	bot.add_cog(Twitter(bot))
