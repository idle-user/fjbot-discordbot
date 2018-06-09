#!/usr/bin/env python3
import tweepy

from credentials import twitter
from dbhandler import DBHandler


dbhandler = DBHandler()

auth = tweepy.OAuthHandler(twitter['consumer_key'], twitter['consumer_secret'])
auth.set_access_token(twitter['access_token'], twitter['access_token_secret'])
api = tweepy.API(auth)
follow_ids = []
tweets = []

class SuperstarListener(tweepy.StreamListener):
	#from fjbot import message_twitter
	def __init__(self, tweet_limit=200):
		self.tweet_limit = tweet_limit
		super(SuperstarListener, self).__init__()
	def on_status(self, status):
		global tweets
		if len(tweets)>self.tweet_limit:
			return False
		# print('TWEET: {}: {}'.format(status.user.screen_name, status.text))
		if not (status.retweeted or 'RT @' in status.text) and status.user.id_str in follow_ids:
			# tweet user_id must be in id and not a retweet
			if not status.in_reply_to_user_id or api.get_user(status.in_reply_to_user_id_str).verified:
				# tweet must be non-reply or reply to verified account
				tweets.append('https://twitter.com/statuses/{}'.format(status.id))
	def on_error(self, status_code):
		print('twitter.SuperstarListener.on_error: {}'.format(status_code))
		if status_code == 420:
			return False

def superstar_tweet_stream(loop):
	global follow_ids
	follow_ids = [s['official_twitter_id'] for s in dbhandler.superstar_twitter()]
	follow_ids.append('7517222') #official WWE twitter
	follow_ids = list(filter(None, follow_ids))
	stream = tweepy.Stream(auth, SuperstarListener())
	stream.filter(follow=follow_ids, async=True)
	#loop.create_task(stream.filter(follow=follow_ids, async=True))

def tweet(msg):
	status = api.update_status(msg)
	link = 'https://twitter.com/statuses/{}'.format(status.id)
	# tweets.append(link)
	return link

def superstar_tweets(id, count=1):
	return api.user_timeline(id=id, count=count, include_rts=False)

def update_twitter_ids():
	print('Updating Superstar Twitter IDs')
	for s in dbhandler.superstar_twitter():
		try:
			user = api.get_user(s['official_twitter'])
			id = user.id_str if user.verified else ''
			dbhandler.superstar_update_twitter_id(s['id'], id)
			if user.verified:
				print('Updated {}: {} ({})'.format(s['name'], s['official_twitter'], id))
			else:
				print('Removed {}: {}. Not verified.'.format(s['name'], s['official_twitter']))
		except:
			print('Error {}: {}'.format(s['name'], s['official_twitter']))

if __name__=='__main__':
	update_twitter_ids()
	#superstar_twitter = dbhandler.superstar_twitter()
	#print('Superstar Tweets')
	#for s in superstar_twitter:
	#	tweet = api.user_timeline(id=s['official_twitter_id'], count=1, include_rts=False)[0]
	#	print('{}:{}:"{}"'.format(s['name'], s['official_twitter'], tweet.text.rstrip('\r\n')))
