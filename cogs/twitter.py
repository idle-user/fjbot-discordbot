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
		self.bot.loop.create_task(self.superstar_tweet_task())
		self.bot.loop.create_task(self.superstar_birthday_task())

	def __unload(self):
		self.stream.running = False

	class StreamListener(tweepy.StreamListener):
		def __init__(self, myapi, follow_ids):
			self.myapi = myapi
			self.follow_ids = follow_ids
			super(Twitter.StreamListener, self).__init__()
		def on_status(self, status):
			# print('TWEET: {}: {}'.format(status.user.screen_name, status.text))
			if not (status.retweeted or 'RT @' in status.text) and status.user.id_str in self.follow_ids:
				# tweet user_id must be in id and not a retweet
				if not status.in_reply_to_user_id or self.myapi.twitter.get_user(status.in_reply_to_user_id_str).verified:
					# tweet must be non-reply or reply to verified account
					tweet = 'https://twitter.com/statuses/{}'.format(status.id)
					self.myapi.buffer.append(tweet)
		def on_error(self, status_code):
			print('Twitter.SuperstarListener.on_error: {}'.format(status_code))
			if status_code == 420:
				return False

	def latest_tweets(self, twitter_id, count=1):
		return self.twitter.user_timeline(id=twitter_id, count=count, include_rts=False)

	def live_tweet(msg):
		status = api.update_status(msg)
		link = 'https://twitter.com/statuses/{}'.format(status.id)
		return link

	def start_stream(self):
		follow_ids = [s['official_twitter_id'] for s in self.bot.dbhandler.superstar_twitter()]
		follow_ids.append('7517222') #official WWE twitter
		follow_ids = list(filter(None, follow_ids))
		self.stream = tweepy.Stream(self.auth, self.StreamListener(self, follow_ids))
		self.stream.filter(follow=follow_ids, async=True)

	async def superstar_tweet_task(self):
		await self.bot.wait_until_ready()
		self.buffer = []
		self.start_stream()
		print('Starting Twitter Stream ...')
		while not self.bot.is_closed and self.stream.running:
			while self.buffer:
				await self.bot.send_message(self.channel_twitter, self.buffer.pop())
			await asyncio.sleep(1)
		print('END superstar_tweet_task')

	async def superstar_birthday_task(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed:
			events = []
			dt = datetime.datetime.now()
			timer = ((24 - dt.hour - 1) * 60 * 60) + ((60 - dt.minute - 1) * 60) + (60 - dt.second)
			for s in self.bot.dbhandler.superstar_birthdays():
				if not s['official_twitter']: continue
				s['dt'] = datetime.datetime(dt.year,  s['dob'].month,  s['dob'].day)
				if s['dt'] > dt:
					if events and events[0]['dt']!=s['dt']: break
					events.append(s)
					timer = (events[0]['dt'] - dt).total_seconds()
			print('birthday_schedule_task: sleep_until:{}, event:{}'.format(dt+datetime.timedelta(seconds=timer), ','.join(e['official_twitter'] for e in events)))
			await asyncio.sleep(timer)
			if events:
				tweet_link = self.live_tweet('Happy Birthday, {}! #WWE #BDAY\n- Sent from everyone at https://discord.gg/Q9mX5hQ #discord #fjbot'.format(', '.join(e['official_twitter'] for e in events)))
				await self.bot.send_message(self.channel_general, tweet_link) 
		print('END birthday_schedule_task')
		
	@commands.command(name='tweet', pass_context=True)
	@checks.is_owner()
	async def send_tweet(self, ctx, message):
		await self.bot.say('Send Tweet? [Y/N]```{}```'.format(message))
		confirm = await self.bot.wait_for_message(timeout=10.0, author=ctx.message.author, check=confirm_check)
		if confirm and confirm.content.upper()=='Y':
			status = self.twitter.update_status(msg)
			tweet_link = 'https://twitter.com/statuses/{}'.format(status.id)
			await self.bot.say(tweet_link)
		else:
			await self.bot.say('Tweet cancelled.')
	
	@commands.command(name='tweets', pass_context=True)
	async def superstar_tweets(self, ctx, *args):
		try:
			superstar = args[0]
			count = int(args[1]) if len(args)>1 else 1
			count = 1 if count<1 else count
			count = 5 if count>5 else count
		except:		
			await self.bot.say('Invalid `!tweets` format.\n`!tweets [superstar] [count]`')
			return
		if superstar.startswith('@'):
			id = superstar
		elif superstar.lower() == 'wwe':
			id = '@WWE'
		else:
			bio = self.bot.dbhandler.superstar_bio('%'+superstar.replace(' ','%')+'%')
			id = bio['official_twitter_id'] if bio else False	
		if id:
			tweets = self.latest_tweets(id, count)
			for tweet in tweets:
				await self.bot.say('https://twitter.com/statuses/{}'.format(tweet.id))
		else:
			await self.bot.say("Unable to find Tweets for '{}'".format(superstar))

def setup(bot):
	bot.add_cog(Twitter(bot))
